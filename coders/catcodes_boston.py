#!/usr/bin/python
#
# Categories are prefixes, i.e. a geocode for "A / B" will apply to "A / B / C".

import coders.registration
import os

# Geocodes categories (generally points of interest) that are specified in cat_codes_boston.txt
class CatCodeCoderBoston:
  def __init__(self):
    self._catmap = {}
    codes = [line.split(" : ") for line in file(os.path.abspath(__file__ + '/../../ma_specific_resources/cat_codes_boston.txt')).read().split("\n") if line]
    assert codes
    for lat_lon, cat in codes:
      lat = float(lat_lon.split(',')[0])
      lon = float(lat_lon.split(',')[1])
      self._catmap[cat.lower()] = (lat, lon)

  def codeRecord(self, r):
    for geocat, lat_lon in self._catmap.iteritems():
      if geocat in r.title().lower():
        return {
            'address': geocat,
            'source': geocat,
            'type': 'point_of_interest',
            'lat' : lat_lon[0], # We set the lat so we don't have to use Google's geocoder later to find it
            'lon' : lat_lon[1]
        }

    return None

  def name(self):
    return 'cat-codes-boston'

  def finalize(self):
    pass

coders.registration.registerCoderClass(CatCodeCoderBoston)