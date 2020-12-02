# Copyright 2018-2020 The UBC EOAS MOAD Group
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Functions to transform an MOHID HDF5 output file into a netCDF4 file.
"""
import logging
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import arrow
import click
import numpy
import tables
import xarray

logging.getLogger(__name__).addHandler(logging.NullHandler())


def hdf5_to_netcdf4(hdf5_file, netcdf4_file):
    """Transform selected contents of a MOHID HDF5 results file HDF5_FILE into a netCDF4 file
    stored as NETCDF4_FILE.
    \f

    :param hdf5_file: File path and name of MOHID HDF5 results file to read from.
    :type hdf5_file: :py:class:`pathlib.Path` or str

    :param netcdf4_file: File path and name of netCDF4 file to write to.
    :type netcdf4_file: :py:class:`pathlib.Path` or str
    """
    with tables.open_file(hdf5_file) as h5file:
        logging.info(f"reading MOHID hdf5 results from: {hdf5_file}")
        timestep_files = []
        with tempfile.TemporaryDirectory(dir=os.environ.get("SLURM_TMPDIR")) as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            netcdf4_file = Path(netcdf4_file)
            grid_indices, timestep_file = _init_dataset(
                h5file, netcdf4_file, tmp_dir_path
            )
            timestep_files.append(timestep_file)
            for index in range(2, h5file.root.Time._v_nchildren + 1):
                timestep_files.append(
                    _calc_timestep_file(
                        grid_indices, h5file, index, netcdf4_file, tmp_dir_path
                    )
                )
            _concat_timestep_files(timestep_files, netcdf4_file)
            oil_times_file = _calc_oil_times_file(
                grid_indices, h5file, netcdf4_file, tmp_dir_path
            )
            _append_oil_times_file(oil_times_file, netcdf4_file)
    logging.info(f"created MOHID netCDF4 results in: {netcdf4_file}")


def _init_dataset(h5file, netcdf4_file, tmp_dir):
    """
    :param :py:class:`tables.File` h5file:
    :param :py:class:`pathlib.Path` netcdf4_file:
    :param :py:class:`pathlib.Path` tmp_dir:
    :rtype: :py:class:`types.SimpleNamespace`, :py:class:`pathlib.Path`
    """
    time_coord = _calc_time_coord(h5file, 1)
    logging.info(f"initializing dataset with fields at: {time_coord.values[0]}")
    z_index, y_index, y_index_lat, x_index, x_index_lat = _calc_zyx_indices(h5file)
    logging.info(
        f"initializing dataset with (z, y, x) grid indices: "
        f"({z_index.size}, {y_index.size}, {x_index.size})"
    )
    data_vars = {}
    for group in h5file.root.Results.OilSpill.Data_2D:
        if group._v_name in ("Beaching Time", "Oil Arrival Time", "Beaching Volume"):
            continue
        data_vars.update(_calc_data_var(group, 1, (time_coord, y_index, x_index)))
        logging.debug(
            f"added (t, y, x) field: {group._v_name} at {time_coord.values[0]}"
        )
    for group in h5file.root.Results.OilSpill.Data_3D:
        data_vars.update(
            _calc_data_var(group, 1, (time_coord, z_index, y_index, x_index))
        )
        logging.debug(
            f"added (t, z, y, x) field: {group._v_name} at {time_coord.values[0]}"
        )
    for group in h5file.root.Grid:
        if group._v_name in ("Latitude"):
            name = group._v_name
            coords = (y_index_lat, x_index_lat)
            field = numpy.swapaxes(group.read(), 0, 1)
            attrs = {
                "standard_name": name,
                "long_name": group._v_name,
                "units": "degrees_north",
            }
            data_vars.update(
                {
                    name: xarray.DataArray(
                        name=name, data=field, coords=coords, attrs=attrs
                    )
                }
            )
            logging.debug(f"added (y, x) field: {group._v_name}")
        elif group._v_name in ("Longitude"):
            name = group._v_name
            coords = (y_index_lat, x_index_lat)
            field = numpy.swapaxes(group.read(), 0, 1)
            attrs = {
                "standard_name": name,
                "long_name": group._v_name,
                "units": "degrees_east",
            }
            data_vars.update(
                {
                    name: xarray.DataArray(
                        name=name, data=field, coords=coords, attrs=attrs
                    )
                }
            )
            logging.debug(f"added (y, x) field: {group._v_name}")
    ds = xarray.Dataset(
        data_vars=data_vars,
        coords={
            time_coord.name: time_coord,
            z_index.name: z_index,
            y_index.name: y_index,
            x_index.name: x_index,
            y_index_lat.name: y_index_lat,
            x_index_lat.name: x_index_lat,
        },
    )
    timestamp = (
        time_coord.values[0].astype("datetime64[m]").astype(str).replace(":", "")
    )
    timestep_file = (tmp_dir / f"{netcdf4_file.stem}_{timestamp}").with_suffix(".nc")
    _write_netcdf(ds, timestep_file)
    logging.info(f"wrote initial time step to: {timestep_file}")
    return (
        SimpleNamespace(z_index=z_index, y_index=y_index, x_index=x_index),
        timestep_file,
    )


def _calc_timestep_file(grid_indices, h5file, index, netcdf4_file, tmp_dir):
    """
    :param :py:class:`types.SimpleNamespace` grid_indices:
    :param :py:class:`tables.File` h5file:
    :param int index:
    :param :py:class:`pathlib.Path` netcdf4_file:
    :param :py:class:`pathlib.Path` tmp_dir:
    :return:
    """
    time_coord = _calc_time_coord(h5file, index)
    logging.info(f"processing fields at: {time_coord.values[0]}")
    data_vars = {}
    for group in h5file.root.Results.OilSpill.Data_2D:
        if group._v_name in ("Beaching Time", "Oil Arrival Time", "Beaching Volume"):
            continue
        data_vars.update(
            _calc_data_var(
                group, index, (time_coord, grid_indices.y_index, grid_indices.x_index)
            )
        )
        logging.debug(
            f"added (t, y, x) field: {group._v_name} at {time_coord.values[0]}"
        )
    for group in h5file.root.Results.OilSpill.Data_3D:
        data_vars.update(
            _calc_data_var(
                group,
                index,
                (
                    time_coord,
                    grid_indices.z_index,
                    grid_indices.y_index,
                    grid_indices.x_index,
                ),
            )
        )
        logging.debug(
            f"added (t, z, y, x) field: {group._v_name} at {time_coord.values[0]}"
        )
    ds = xarray.Dataset(
        data_vars=data_vars,
        coords={
            time_coord.name: time_coord,
            grid_indices.z_index.name: grid_indices.z_index,
            grid_indices.y_index.name: grid_indices.y_index,
            grid_indices.x_index.name: grid_indices.x_index,
        },
    )
    timestamp = time_coord.values[0].astype("datetime64[m]").astype(str)
    timestep_file = (tmp_dir / f"{netcdf4_file.stem}_{timestamp}").with_suffix(".nc")
    _write_netcdf(ds, timestep_file)
    logging.info(f"wrote time step to: {timestep_file}")
    return timestep_file


def _concat_timestep_files(timestep_files, netcdf4_file):
    """
    :param list timestep_files:
    :param :py:class:`pathlib.Path`netcdf4_file:
    """
    ncrcat_cmd = "ncrcat -4 -L4 -O -o"
    input_files = " ".join(os.fspath(f) for f in timestep_files)
    cmd = f"{ncrcat_cmd} {netcdf4_file} {input_files}"
    logging.debug(f"concatenating time steps with: {ncrcat_cmd} {netcdf4_file}")
    proc = subprocess.run(shlex.split(cmd), capture_output=True, check=True, text=True)
    expected_msg = "ncrcat: INFO/WARNING Multi-file concatenator encountered packing attribute scale_factor"
    if proc.stderr and not proc.stderr.startswith(expected_msg):
        logging.error(proc.stderr)
    logging.info(f"concatenated time steps to: {netcdf4_file}")


def _calc_oil_times_file(grid_indices, h5file, netcdf4_file, tmp_dir):
    """
    :param :py:class:`types.SimpleNamespace` grid_indices:
    :param :py:class:`tables.File` hdf5_file:
    :param :py:class:`pathlib.Path` netcdf4_file:
    :param :py:class:`pathlib.Path` tmp_dir:
    :rtype: :py:class:`pathlib.Path`
    """
    logging.info(f"processing oil beaching and arrival times")
    time_coord = _calc_time_coord(h5file, 1)
    data_vars = {}
    var_timebases = {
        "Beaching Time": time_coord.values[0],
        "Oil Arrival Time": time_coord.values[0],
        "Beaching Volume": None,
    }
    for group in h5file.root.Results.OilSpill.Data_2D:
        if group._v_name not in var_timebases:
            continue

        data_vars.update(
            _calc_data_var(
                group,
                group._v_nchildren,
                (grid_indices.y_index, grid_indices.x_index),
                timebase=var_timebases[group._v_name],
            )
        )

        logging.debug(
            f"added (y, x) field: {group._v_name} at time step {group._v_nchildren}"
        )
    ds = xarray.Dataset(
        data_vars=data_vars,
        coords={
            grid_indices.y_index.name: grid_indices.y_index,
            grid_indices.x_index.name: grid_indices.x_index,
        },
    )
    oil_times_file = (tmp_dir / f"{netcdf4_file.stem}_oil_times").with_suffix(".nc")
    _write_netcdf(ds, oil_times_file, time_coord=False, scaled_vars=False)
    logging.info(f"wrote oil beaching and arrival times to: {oil_times_file}")
    return oil_times_file


def _append_oil_times_file(oil_times_file, netcdf4_file):
    """
    :param :py:class:`pathlib.Path` oil_times_file:
    :param :py:class:`pathlib.Path` netcdf4_file:
    """
    ncks_cmd = "ncks -4 -L4 -A"
    cmd = f"{ncks_cmd} {oil_times_file} {netcdf4_file}"
    logging.debug(f"appending oil times file with: {cmd}")
    proc = subprocess.run(shlex.split(cmd), capture_output=True, check=True, text=True)
    if proc.stderr:
        logging.error(proc.stderr)
    logging.info(f"appended oil times file to: {netcdf4_file}")


def _calc_time_coord(hdf5_file, index):
    """
    :param int index:
    :param :py:class:`tables.File` h5file:
    :rtype: :py:class:`xarray.DataArray`
    """
    time_step = getattr(hdf5_file.root.Time, f"Time_{index:05d}")
    time_coord = xarray.DataArray(
        name="time",
        data=[arrow.get(*time_step.read().astype(int)).naive],
        dims="time",
        attrs={"standard_name": "time", "long_name": "time", "tz_name": "UTC"},
    )
    return time_coord


def _calc_zyx_indices(h5file):
    """
    :param :py:class:`tables.File` h5file:
    :rtype: 3-tuple of :py:class:`xarray.DataArray`
    """
    oil_conc_3d = h5file.root.Results.OilSpill.Data_3D.OilConcentration_3D
    latitude = h5file.root.Grid.Latitude
    z_count, x_count, y_count = oil_conc_3d.OilConcentration_3D_00001.shape
    x_count_lat, y_count_lat = latitude.shape
    z_index = xarray.DataArray(
        name="grid_z",
        data=numpy.arange(z_count, dtype=numpy.int16),
        dims="grid_z",
        attrs={"standard_name": "model_level_index", "long_name": "depth level"},
    )
    y_index = xarray.DataArray(
        name="grid_y",
        data=numpy.arange(y_count, dtype=numpy.int16),
        dims="grid_y",
        attrs={"standard_name": "model_y_index", "long_name": "y index"},
    )
    y_index_lat = xarray.DataArray(
        name="grid_y_latlon",
        data=numpy.arange(y_count_lat, dtype=numpy.single),
        dims="grid_y_latlon",
        attrs={
            "standard_name": "model_latlon_y_index",
            "long_name": "latlon y index",
            "units": "degrees_north",
        },
    )
    x_index = xarray.DataArray(
        name="grid_x",
        data=numpy.arange(x_count, dtype=numpy.int16),
        dims="grid_x",
        attrs={"standard_name": "model_x_index", "long_name": "x index"},
    )
    x_index_lat = xarray.DataArray(
        name="grid_x_latlon",
        data=numpy.arange(x_count_lat, dtype=numpy.single),
        dims="grid_x_latlon",
        attrs={
            "standard_name": "model_latlon_x_index",
            "long_name": "latlon x index",
            "units": "degrees_east",
        },
    )
    return z_index, y_index, y_index_lat, x_index, x_index_lat


def _calc_data_var(group, index, coords, timebase=None):
    """
    :param :py:class:`tables.Group` group:
    :param int index:
    :param tuple coords:
    :param :py:class:`numpy.datetime64` timebase:
    :rtype: :py:class:`xarray.DataArray`
    """
    name = group._v_name.replace(" ", "_")
    field = getattr(group, f"{group._v_name}_{index:05d}")
    units = field.attrs["Units"].decode()
    da_field = (
        numpy.swapaxes(field.read(), 1, 2)
        if len(coords) == 4
        else numpy.swapaxes(field.read(), 0, 1)
    )
    data = da_field if len(coords) == 2 else numpy.expand_dims(da_field, axis=0)
    attrs = {"standard_name": name, "long_name": group._v_name, "units": units}
    if timebase is not None:
        data = data.astype("timedelta64[s]") + timebase
        attrs = {"standard_name": name, "long_name": group._v_name}
    return {name: xarray.DataArray(name=name, data=data, coords=coords, attrs=attrs)}


def _write_netcdf(ds, netcdf4_file, time_coord=True, scaled_vars=True):
    """
    :param :py:class:`xarray.Dataset` ds:
    :param :py:class:`pathlib.Path` netcdf4_file:
    :param boolean time_coord:
    :param boolean scaled_vars:
    """
    encoding = {}
    if time_coord:
        encoding.update(
            {
                "time": {
                    "dtype": numpy.float64,
                    "units": "seconds since 1970-01-01T00:00:00Z",
                }
            }
        )
    if scaled_vars:
        for var in ds.data_vars:
            encoding.update(
                {var: {"dtype": numpy.int32, "scale_factor": 1e-4, "_FillValue": -9999}}
            )
    ds.to_netcdf(
        netcdf4_file,
        mode="w",
        format="NETCDF4",
        encoding=encoding,
        unlimited_dims=("time",),
        compute=True,
    )


@click.command(help=hdf5_to_netcdf4.__doc__)
@click.version_option()
@click.argument("hdf5_file", type=click.Path(exists=True))
@click.argument("netcdf4_file", type=click.Path(writable=True))
@click.option(
    "-v",
    "--verbosity",
    default="warning",
    show_default=True,
    type=click.Choice(("debug", "info", "warning", "error", "critical")),
    help="""
        Choose how much information you want to see about the progress of the transformation;
        warning, error, and critical should be silent unless something bad goes wrong. 
    """,
)
def cli(hdf5_file, netcdf4_file, verbosity):
    """Command-line interface for :py:func:`moad_tools.midoss.hdf5_to_netcdf4`.

    Please see:

      hdf5-to-netcdf4 --help

    :param str hdf5_file: File path and name of MOHID HDF5 results file to read from.

    :param str netcdf4_file: File path and name of netCDF4 file to write to.

    :param str verbosity: Verbosity level of logging messages about the progress of the
                          transformation.
                          Choices are :kbd:`debug, info, warning, error, critical`.
                          :kbd:`warning`, :kbd:`error`, and :kbd:`critical` should be silent
                          unless something bad goes wrong.
                          Default is :kbd:`warning`.
    """
    logging_level = getattr(logging, verbosity.upper())
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s hdf5-to-netcdf4 %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    hdf5_to_netcdf4(hdf5_file, netcdf4_file)
