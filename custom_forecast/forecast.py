from pydap.client import open_url

import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser


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
                        ddsPath = value[:-4]
                        self.ddsFiles.append(ddsPath)
        return

    def listEntries(self, offsetStart, offsetEnd):
        return self.ddsFiles[offsetStart:offsetEnd]


def getUrls(offsetStart, offsetEnd):
    """
    Get the URL from the page, starting from the end, and count
    backward "offset" times
    """
    # Note: This page should be used, but pydap does not support it's format yet:
    # http://portal.nccs.nasa.gov/cgi-lats4d/opendap.cgi?&path=/GEOS-5/fp/0.25_deg/fcast/tavg1_2d_slv_Nx
    parser = DDSParser()
    listUrl = 'http://opendap.nccs.nasa.gov/dods/GEOS-5/fp/0.25_deg/fcast/tavg1_2d_slv_Nx'
    list_ = urllib.request.urlopen(listUrl)
    html = list_.read()
    parser.feed(html.decode())
    urls = parser.listEntries(offsetStart, offsetEnd)
    return urls


def toLatLongIndex(lat, lon, shape):
    iLat = int((shape[1]/2) + 1/0.25 * lat)
    iLon = int((shape[2]/2) - 1/0.3125 * lon) + 1
    return iLat, iLon


def getPressure(lat, lon, url, dataset=None):
    if not dataset:
        dataset = open_url(url)
    # slp = sea level pressure (I think?)
    var = dataset['slp']
    # numHours = var.array.shape[0]
    # Get all of the data for this position at once
    iLat, iLon = toLatLongIndex(lat, lon, var.array.shape)
    # grid, t, la, lo = var[0:numHours, iLat, iLon]
    grid, t, la, lo = var[:, iLat, iLon]
    # Create a pressure list and a time list
    pList = grid.data.reshape((grid.data.size,)) / 1000
    tList = t.data.reshape((t.data.size,)) - 1
    # Return the pressures and times, along with the lat/long from the forecast
    return pList, tList, float(la[0]), float(lo[0])
