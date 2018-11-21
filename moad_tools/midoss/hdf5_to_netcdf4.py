# Copyright 2018 The UBC EOAS MOAD Group
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
"""Functions to transform an MOHID HDF5 output file into an xarray dataset.
"""
import functools
import logging
import time
from types import SimpleNamespace

import arrow
import numpy
import tables
import xarray

# logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.getLogger(__name__)


t0 = 0


def main_timer(func):
    @functools.wraps(func)
    def wrapper_main_timer(*args, **kwargs):
        global t0
        t0 = time.time()
        return_value = func(*args, **kwargs)
        logging.info(f"total time: {time.time() - t0}")
        return return_value

    return wrapper_main_timer


def function_timer(func):
    @functools.wraps(func)
    def wrapper_function_timer(*args, **kwargs):
        t_func = time.time()
        return_value = func(*args, **kwargs)
        logging.info(
            f"function time: {time.time() - t_func}; total time: {time.time() - t0}"
        )
        return return_value

    return wrapper_function_timer


@main_timer
def hdf5_to_netcdf4(hdf5_file, nc_file_dir, nc_filename_root):
    """Transform selected contents of a MOHID HDF5 results file into a netCDF4 file.

    :param hdf5_file: File path and name of MOHID HDF5 results file to read from.
    :type hdf5_file: :py:class:`pathlib.Path` or str

    :param nc_file_dir: File path and name of netCDF4 file to write to.
    :type nc_file_dir: :py:class:`pathlib.Path` or str

    :param nc_filename_root:
    """
    with tables.open_file(hdf5_file) as h5file:
        logging.info(f"reading MOHID results from: {hdf5_file}")
        timestep_files = []
        grid_indices, timestep_file = _init_dataset(
            h5file, nc_file_dir, nc_filename_root
        )
        timestep_files.append(timestep_file)
        # for index in range(2, h5file.root.Time._v_nchildren + 1):
        for index in range(2, 4):
            timestep_files.append(
                _calc_timestep_file(
                    grid_indices, h5file, index, nc_file_dir, nc_filename_root
                )
            )
        # oil_times_file = _calc_oil_times_file(grid_indices, h5file, nc_file_dir, nc_filename_root)


@function_timer
def _init_dataset(h5file, nc_file_dir, nc_filename_root):
    time_coord = _calc_time_coord(h5file, 1)
    logging.info(f"initializing dataset with fields at: {time_coord.values[0]}")
    z_index, y_index, x_index = _calc_zyx_indices(h5file)
    logging.info(
        f"initializing dataset with (z, y, x) grid indices: "
        f"({z_index.size}, {y_index.size}, {x_index.size})"
    )
    data_vars = {}
    for group in h5file.root.Results.OilSpill.Data_2D:
        if group._v_name in ("Beaching Time", "Oil Arrival Time"):
            continue
        data_vars.update(_calc_data_var(group, 1, (time_coord, y_index, x_index)))
        logging.info(
            f"added (t, y, x) field: {group._v_name} at {time_coord.values[0]}"
        )
    for group in h5file.root.Results.OilSpill.Data_3D:
        data_vars.update(
            _calc_data_var(group, 1, (time_coord, z_index, y_index, x_index))
        )
        logging.info(
            f"added (t, z, y, x) field: {group._v_name} at {time_coord.values[0]}"
        )
    ds = xarray.Dataset(
        data_vars=data_vars,
        coords={
            time_coord.name: time_coord,
            z_index.name: z_index,
            y_index.name: y_index,
            x_index.name: x_index,
        },
    )
    timestamp = (
        time_coord.values[0].astype("datetime64[m]").astype(str).replace(":", "")
    )
    nc_file = nc_file_dir / f"{nc_filename_root}_{timestamp}.nc"
    _write_netcdf(ds, nc_file)
    logging.info(f"wrote initial time step to: {nc_file}")
    return SimpleNamespace(z_index=z_index, y_index=y_index, x_index=x_index), nc_file


@function_timer
def _calc_timestep_file(grid_indices, h5file, index, nc_file_dir, nc_filename_root):
    time_coord = _calc_time_coord(h5file, index)
    logging.info(f"processing fields at: {time_coord.values[0]}")
    data_vars = {}
    for group in h5file.root.Results.OilSpill.Data_2D:
        if group._v_name in ("Beaching Time", "Oil Arrival Time"):
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
    hr = time_coord.values[0].astype("datetime64[m]").astype(str)
    nc_file = nc_file_dir / f"{nc_filename_root}_{hr}.nc"
    _write_netcdf(ds, nc_file)
    logging.debug(f"wrote time step to: {nc_file}")
    return nc_file


@function_timer
def _calc_oil_times_file(grid_indices, h5file, nc_file_dir, nc_filename_root):
    logging.info(f"processing oil beaching and arrival times")
    data_vars = {}
    for group in h5file.root.Results.OilSpill.Data_2D:
        if group._v_name not in ("Beaching Time", "Oil Arrival Time"):
            continue
        data_vars.update(
            _calc_data_var(
                group, group._v_nchildren, (grid_indices.y_index, grid_indices.x_index)
            )
        )
        logging.info(
            f"added (y, x) field: {group._v_name} at time step {group._v_nchildren}"
        )
    ds = xarray.Dataset(
        data_vars=data_vars,
        coords={
            grid_indices.y_index.name: grid_indices.y_index,
            grid_indices.x_index.name: grid_indices.x_index,
        },
    )
    nc_file = nc_file_dir / f"{nc_filename_root}_oil_times.nc"
    _write_netcdf(ds, nc_file, time_coord=False, scaled_vars=False)
    logging.debug(f"wrote oil beaching and arrival times to: {nc_file}")
    return nc_file


def _calc_time_coord(h5file, index):
    """
    :param index:
    :param :py:class:`tables.File` h5file:
    :rtype: :py:class:`xarray.DataArray`
    """
    time_step = getattr(h5file.root.Time, f"Time_{index:05d}")
    time_coord = xarray.DataArray(
        name="time",
        data=[arrow.get(*time_step.read().astype(int)).datetime],
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
    z_count, x_count, y_count = oil_conc_3d.OilConcentration_3D_00001.shape
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
    x_index = xarray.DataArray(
        name="grid_x",
        data=numpy.arange(x_count, dtype=numpy.int16),
        dims="grid_x",
        attrs={"standard_name": "model_x_index", "long_name": "x index"},
    )
    return z_index, y_index, x_index


def _calc_data_var(group, index, coords):
    """
    :param group:
    :param int index:
    :param 3-tuple coords:
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
    return {
        name: xarray.DataArray(
            name=name,
            data=data,
            coords=coords,
            attrs={"standard_name": name, "long_name": group._v_name, "units": units},
        )
    }


def _write_netcdf(ds, nc_file, time_coord=True, scaled_vars=True):
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
        nc_file,
        mode="w",
        format="NETCDF4",
        encoding=encoding,
        unlimited_dims=("time",),
        compute=True,
    )
