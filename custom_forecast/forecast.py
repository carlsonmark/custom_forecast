import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from threading import Lock

import cachetools.func
import numpy as np
import pandas as pd
from data_cache import pandas_cache
from pydap.client import open_url
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.signal import savgol_filter

data_source_lock = Lock()


class DDSParser(HTMLParser):

    def __init__(self):
        self.ddsFiles = []
        HTMLParser.__init__(self)
        return

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            for attr, value in attrs:
                if attr.lower() == 'href':
                    if '.dds' in value:
                        # Strip .dds from the end
                        dds_path = value[:-4]
                        self.ddsFiles.append(dds_path)
        return

    def list_entries(self, offset_start, offset_end):
        return self.ddsFiles[offset_start:offset_end]


# Limit the number of calls to one per hour. New forecasts are only available
# once every few hours anyway.
@cachetools.func.ttl_cache(maxsize=16, ttl=60 * 60)
def get_urls(offset_start, offset_end):
    """
    Get the URL from the page, starting from the end, and count
    backward "offset" times
    """
    # Note: This page should be used, but pydap does not support it's format yet:
    # http://portal.nccs.nasa.gov/cgi-lats4d/opendap.cgi?&path=/GEOS-5/fp/0.25_deg/fcast/tavg1_2d_slv_Nx
    parser = DDSParser()
    list_url = 'http://opendap.nccs.nasa.gov/dods/GEOS-5/fp/0.25_deg/fcast/tavg1_2d_slv_Nx'
    print(f'Getting URLs from {list_url}')
    list_ = urllib.request.urlopen(list_url)
    html = list_.read()
    parser.feed(html.decode())
    urls = parser.list_entries(offset_start, offset_end)
    return urls


def to_lat_long_index(lat, lon, shape):
    i_lat = int((shape[1] / 2) + 1 / 0.25 * lat)
    i_lon = int((shape[2] / 2) - 1 / 0.3125 * lon) + 1
    return i_lat, i_lon


def get_pressure(lat, lon, url, dataset=None):
    if not dataset:
        dataset = open_url(url)
    # slp = sea level pressure (I think?)
    var = dataset['slp']
    # numHours = var.array.shape[0]
    # Get all the data for this position at once
    i_lat, i_lon = to_lat_long_index(lat, lon, var.array.shape)
    # grid, t, la, lo = var[0:numHours, iLat, iLon]
    data = var[:, i_lat, i_lon]
    lat = data['lat'].data[0]
    lon = data['lon'].data[0]
    t = data['time']
    grid = data['slp']
    # Create a pressure list and a time list
    p_list = grid.data.reshape((grid.data.size, )) / 1000
    t_list = t.data.reshape((t.data.size, )) - 1
    # Return the pressures and times, along with the lat/long from the forecast
    return p_list, t_list, lat, lon


def pressure_derivative(pressure: pd.array,
                        derivative_scale: float = 20) -> pd.array:
    x = np.arange(len(pressure))
    filtered_pressure = savgol_filter(pressure, len(pressure) // 8, 3)
    f = InterpolatedUnivariateSpline(x, filtered_pressure, k=1)
    derivative = f.derivative()(x) * derivative_scale
    return derivative


# Getting data from the server is incredibly slow, so use a cache.
# pandas_cache is disk based, so it persists across restarts of the process,
# which helps a lot when developing the code.
@pandas_cache
def data_frame(url: str):
    print(f'Getting: {url}')
    pressure, time_, lat, lon = get_pressure(51.05, 114.0677, url)
    # It seems like the time offset is not needed now?
    # time_offset = (-time.timezone) / (24.0 * 3600.0)
    # time_with_offset = time_ + time_offset
    ordinal_date = time_.astype(int)
    fractional_date = time_ - ordinal_date
    seconds = (fractional_date * (24 * 60 * 60)).astype(int)
    timestamp = pd.array([pd.Timestamp.fromordinal(d) for d in ordinal_date])
    timedelta = pd.array([pd.Timedelta(seconds=s) for s in seconds])
    df = pd.DataFrame(
        dict(time=timestamp + timedelta,
             pressure=pressure,
             derivative=pressure_derivative(pressure)))
    return df


def latest_data_frames():
    with data_source_lock:
        urls = get_urls(-5, None)
        data_frames = [data_frame(url) for url in urls]
    return data_frames
