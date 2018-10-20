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
"""UBC MOAD group geographic places information.

It is recommended that library code that uses the :py:data:`PLACES` data
structure from this module should use :kbd:`try...except` to catch
:py:exc:`KeyError` exceptions and produce an error message that is more
informative than the default, for example:

.. code-block:: python

    try:
        stn_number = f"{PLACES[stn_id]['stn number']}"
    except KeyError as e:
        raise KeyError(f"place name or info key not found in moad_tools.places.PLACES: {e}")
"""

#: Information about geographic places used in the analysis and presentation of
#: UBC EOAS MOAD group model results.
PLACES = {
    # Wave buoys
    "Halibut Bank": {
        # deg E, deg N
        "lon lat": (-123.72, 49.34),
        # indices of nearest NEMO model grid point
        # j is the latitude (y) direction, i is the longitude (x) direction
        "NEMO grid ji": (503, 261),
        # indices of nearest weather forcing grid point
        # j is the latitude (y) direction, i is the longitude (x) direction
        "GEM2.5 grid ji": (149, 141),
        # ECCC or NOAA buoy number
        "EC buoy number": 46146,
    },
    "Sentry Shoal": {
        "lon lat": (-125.0, 49.92),
        "NEMO grid ji": (707, 145),
        "GEM2.5 grid ji": (183, 107),
        "EC buoy number": 46131,
    },
    # VHFR FVCOM model HADCP station
    "2nd Narrows Rail Bridge": {
        "lon lat": (-123.0247222, 49.2938889),
        "stn number": 3160171,  # AIS MMSI (Maritime Mobile Service Identity)
    },
}
