import time

def ordinalUtc2localtime(utc):
    offset = (-time.timezone) / (24.0 * 3600.0)
    return utc + offset
