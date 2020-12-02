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
"""UBC MOAD group tools regarding gridding and geography."""

import datetime

import numpy as np
import scipy.interpolate as interpolate
import xarray as xr


def make_mapping_file(
    coordinate_file,
    mapping_file,
    grid_description,
    lon_var="nav_lon",
    lat_var="nav_lat",
):
    """Make two arrays that index from longitude and latitude to grid index
    The indices and information to use them are written to a netCDF file
    and the same values are returned by the function.

    :param str coordinate_file: netCDF file to read the coordinates from

    :param str mapping_file: netCDF file written with the index arrays

    :param str grid_description: name of the grid that is being mapped, to be
               written as a comment into the netcdf file

    :param str lon_var: name of longitude variable in the coordinate file

    :param str lat_var: name of latitude variable in the coordinate file

    :return: lonmin, latmin: start of the indexes
             dlon, dlat: step size for the indexes
             indexi, indexj: index arrays
    """
    # get the coordinates
    coords = xr.open_dataset(coordinate_file)
    nav_lons = np.array(coords[lon_var][:])
    nav_lats = np.array(coords[lat_var][:])
    dimensions = nav_lons.shape
    # calculate 1/4 of the grid size
    dlon = (
        max(abs(nav_lons[1, 1] - nav_lons[0, 0]), abs(nav_lons[0, 1] - nav_lons[1, 0]))
        / 4.0
    )
    dlat = (
        max(abs(nav_lats[1, 1] - nav_lats[0, 0]), abs(nav_lats[0, 1] - nav_lats[1, 0]))
        / 4.0
    )
    # flatten the arrays, find domain corners
    nav_lons = np.ndarray.flatten(nav_lons)
    nav_lats = np.ndarray.flatten(nav_lats)
    lonmax, latmax = nav_lons.max(), nav_lats.max()
    lonmin, latmin = nav_lons.min(), nav_lats.min()
    # find the quarter resolution lon/lat grid
    lons1 = np.arange(lonmin, lonmax, dlon)
    lats1 = np.arange(latmin, latmax, dlat)
    lons, lats = np.meshgrid(lons1, lats1)
    # set index arrays
    iis = np.ndarray.flatten(
        np.tile(np.arange(dimensions[0]), (dimensions[1], 1)).transpose()
    )
    jjs = np.ndarray.flatten(np.tile(np.arange(dimensions[1]), (dimensions[0], 1)))
    # grid the indexes on the lon/lat grid
    indexi = interpolate.griddata(
        (nav_lons, nav_lats), iis, (lons, lats), method="nearest"
    ).astype(int)
    indexj = interpolate.griddata(
        (nav_lons, nav_lats), jjs, (lons, lats), method="nearest"
    ).astype(int)

    # write the file
    dims = ("index_lat", "index_lon")
    coords = {"index_lat": lats1, "index_lon": lons1}
    attrs = {"units": "None"}
    da = {}
    da["i"] = xr.DataArray(
        data=indexi, name="Value of I index", dims=dims, coords=coords, attrs=attrs
    )
    da["j"] = xr.DataArray(
        data=indexj, name="Value of J index", dims=dims, coords=coords, attrs=attrs
    )
    da["dlon"] = xr.DataArray(
        data=dlon, name="grid size in longitude", attrs={"units": "Degrees Longitude"}
    )
    da["dlat"] = xr.DataArray(
        data=dlat, name="grid size in latitude", attrs={"units": "Degrees Latitude"}
    )
    da["lonmin"] = xr.DataArray(
        data=lonmin,
        name="minimum longitude value",
        attrs={"units": "Degrees Longitude"},
    )
    da["latmin"] = xr.DataArray(
        data=latmin, name="minimum latitude value", attrs={"units": "Degrees Latitude"}
    )
    data_vars = {
        "indexi": da["i"],
        "indexj": da["j"],
        "dlon": da["dlon"],
        "dlat": da["dlat"],
        "lonmin": da["lonmin"],
        "latmin": da["latmin"],
    }
    ds_attrs = {
        "creator_name": "MOAD Project Contributors",
        "institution": "UBC EOAS",
        "institution_fullname": "Earth, Ocean & Atmospheric Sciences, University of British Columbia",
        "summary": f"Mapping from lons and lats to {grid_description} grid",
        "source": "http:/bitbucket.org/UBC_MOAD/moad_tools/grid_tools.py",
        "history": (
            f"[{datetime.datetime.today().strftime('%Y-%m-%d')}] File creation."
        ),
    }

    ds = xr.Dataset(data_vars, coords, attrs=ds_attrs)
    ds.to_netcdf(path=mapping_file)

    return lonmin, latmin, dlon, dlat, indexi, indexj


def estimate_closest_point(dataset, lons, lats):
    """Estimate the closest grid point to an array of lat/lons
    using a index file created by make_mapping_file above

    :param xarray dataset: dataset

    :param numpy array or list: lons

    :param numpy array or list: lats

    return: numpy array of indexes: iis, jjs
    """
    indexi, indexj = np.array(dataset["indexi"]), np.array(dataset["indexj"])
    lonmin, latmin = dataset["lonmin"].values, dataset["latmin"].values
    dlon, dlat = dataset["dlon"].values, dataset["dlat"].values
    iis = indexi[
        (np.round((lats - latmin) / dlat)).astype(int),
        (np.round((lons - lonmin) / dlon)).astype(int),
    ]
    jjs = indexj[
        (np.round((lats - latmin) / dlat)).astype(int),
        (np.round((lons - lonmin) / dlon)).astype(int),
    ]
    return iis, jjs
