# Copyright 2018 – present The UBC EOAS MOAD Group
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

# SPDX-License-Identifier: Apache-2.0


"""Functions for downloading observations data from web services.
"""
import logging
import urllib.error

import pandas

from moad_tools.places import PLACES

logging.getLogger(__name__).addHandler(logging.NullHandler())


def get_ndbc_buoy(buoy_id):
    """Retrieve a collection of time series of the last 45 days of real-time observed
    buoy data for an ECCC or NOAA data buoy from the NOAA National Data Buoy Center (NDBC)
    https://www.ndbc.noaa.gov/data/realtime2/ web service.

    The time series is returned as a :py:class:`pandas.DataFrame` object.

    The returned time series date/time index is UTC.

    :param int or str buoy_id: Buoy number or name.
                               Names use :py:obj:`moad_tools.places.PLACES` to
                               look up the buoy number.

    :return: Buoy data time series.
    :rtype: :py:class:`pandas.DataFrame`
    """
    endpoint = "https://www.ndbc.noaa.gov/data/realtime2/"
    msg = f"retrieving available real-time buoy data from {endpoint}"
    try:
        buoy_number = int(buoy_id)
    except ValueError:
        try:
            buoy_number = f"{PLACES[buoy_id]['EC buoy number']}"
        except KeyError as exc:
            logging.error(
                f"buoy id not found in places.PLACES: {buoy_id}; "
                f"maybe try an integer buoy number?"
            )
            raise KeyError(
                f"place name or info key not found in moad_tools.places.PLACES: {exc}"
            )

    msg = " ".join(
        (
            msg,
            f"for buoy {buoy_number}"
            if int(buoy_number) == buoy_id
            else f"for buoy {buoy_number} {buoy_id}",
        )
    )
    logging.info(msg)
    ndbc_url = f"{endpoint}{buoy_number}.txt"

    try:
        try:
            df = pandas.read_csv(
                ndbc_url,
                delim_whitespace=True,
                header=[0, 1],
                na_values="MM",
                parse_dates=[[0, 1, 2, 3, 4]],
                date_parser=lambda x: pandas.to_datetime(x, format="%Y %m %d %H %M"),
            )
        except urllib.error.URLError:
            # Work around SSL: UNKNOWN_PROTOCOL error that appeared on 23may18
            # by trying HTTP instead of HTTPS
            ndbc_url = ndbc_url.replace("https://", "http://")
            df = pandas.read_csv(
                ndbc_url,
                delim_whitespace=True,
                header=[0, 1],
                na_values="MM",
                parse_dates=[[0, 1, 2, 3, 4]],
                date_parser=lambda x: pandas.to_datetime(x, format="%Y %m %d %H %M"),
            )
    except urllib.error.HTTPError as exc:
        msg = (
            f"buoy data request failed: HTTP Error {exc.code}: {exc.reason}: {ndbc_url}"
        )
        logging.error(msg)
        raise ValueError(msg) from exc

    columns = {
        "('#YY', '#yr')_('MM', 'mo')_('DD', 'dy')_('hh', 'hr')_('mm', 'mn')": "time"
    }
    columns.update({t: f"{t[0]} [{t[1]}]" for t in df.columns[1:]})
    df = df.rename(index=str, columns=columns).set_index("time").sort_index()
    return df
