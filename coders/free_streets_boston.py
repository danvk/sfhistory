#!/usr/bin/python

import record
import re
import coders.registration
import os
from locatable import LatLonDistance
from collections import defaultdict

DEFAULT_CITY = "Charlestown, MA" # Used to help guide Google's geocoder.  Modify this freely before geocoding pickled data
MAX_BOUND_SIZE = 1000

# Some things look like addresses (e.g. '1939 Golden Gate Expo', '38 Geary bus
# line') but are not.
def should_reject_address(addr):
  if re.search(r'\b(bus|line)\b', addr):
    return True
  if re.search(r'of ^(\d+)', addr):
    return True
  return False


class FreeStreetBostonCoder:
  def __init__(self):
    street_list = open(os.path.abspath(__file__ + '/../../ma_specific_resources/boston_streets.txt')).read().split("\n")
    street_list = [s.lower() for s in street_list if s and not "#" in s] # Ignore lines that are comments

    street_re = '(?:' + '|'.join(street_list) + ')'
    suffix_re = '(?:street|st\.?|avenue|ave\.?|blvd\.?|boulevard|drive|dr\.?)'
    dir_re = '(?:north|south|east|west|northwest|northeast|southwest|southeast)'
    self.addr_re = r'[-0-9]{2,} +' + street_re + r' +(street|st|avenue|ave|road|boulevard|blvd|place|way|bus|line|express bus|area|rush)?'
    
    # Matches streets without addresses.  We require the word street|st|avenue|etc... since we have no number and want to have some confidence.
    self.addr_re_no_number = street_re + r' +(street|st|avenue|ave|road|boulevard|blvd|place|way|bus|line|express bus|area|rush)+'

    # There's some overlap here, but they're in decreasing order of confidence.
    # More confident (i.e. longer) forms get matched first.
    forms = [
      # A between B and C (47; sparse, but "protects" the next forms)
      '(' + street_re + '(?: +street|st\.)?),? +between +(' + street_re + ' (?:street )?)(?:and|&) +(' + street_re + r')\b',

      '(' + street_re + ' +' + suffix_re + ') +(?:and|&|at) +(' + street_re + ' +' + suffix_re + ')',  # A street and B street

      # Funston Avenue, north from Rockridge Drive
      '(' + street_re + ' +' + suffix_re + '?),? ' + dir_re + ' +(?:from|of) +(' + street_re + ' +' + suffix_re + '?)',

      '(' + street_re + ') +(?:and|&|at) +(' + street_re + ' +street)s',         # A and B streets (1027 records)
      '(' + street_re + ') +(?:and|&|at) +(' + street_re + ' +st)s',             # A and B sts (46 records)
      '(' + street_re + ') +(?:and|&|at) +(' + street_re + r' +' + suffix_re + r')\b',  # A and B st/street (193)
      '(' + street_re + ' +' + suffix_re + ') +(?:and|&|at) +(' + street_re + r')\b',  # A street and B

      '(' + street_re + ') +& +(' + street_re + r'\b)',  # A & B (106)
      '(?:at|of|on) (' + street_re + ') +and +(' + street_re + r'\b)',  # at A and B (104)

      # Rejected forms:
      # street_re + ' +and +' + street_re,  # A and B (235 but w/ lots of false positives)
    ]
    self._forms = [re.compile(form) for form in forms]
    self._stats = defaultdict(int)

  def codeRecord(self, r):
    description = coders.sf_streets.clean_street(record.CleanTitle(r.description()).lower())

    # Look for an exact address.
    m = re.search(self.addr_re, description)
    if m:
      addr = m.group(0)
      if not should_reject_address(addr):
        return {
          'address': '{0} {1}'.format(addr, DEFAULT_CITY),
          'source': 'Source Not Set',
          'type': 'street_address'
        }

    # Common cross-street patterns.
    for idx, pat in enumerate(self._forms):
      m = re.search(pat, description)
      if m:
        self._stats[str(1 + idx)] += 1
        if idx != 0: # Index 0 is a regex for A between B and C
          return {
            'address': '{0} and {1} {2}'.format(m.group(1), m.group(2), DEFAULT_CITY),
            'source': 'Source Not Set',
            'type': 'intersection'
          }
        else:
          return {
            'original_address': {
              'address': '{0}'.format(m.group(0), DEFAULT_CITY)
            },
            'split_addresses':
              [{
                'address': '{0} and {1} {2}'.format(m.group(1), m.group(2), DEFAULT_CITY),
                'source': 'Source Not Set',
                'type': 'intersection'
              },
              {
                'address': '{0} and {1} {2}'.format(m.group(1), m.group(3), DEFAULT_CITY),
                'source': 'Source Not Set',
                'type': 'intersection'
              }]
          }
          
    # Look for an address without a street number, google defaults to the center of the street.
    m = re.search(self.addr_re_no_number, description)
    if m:
      addr = m.group(0)
      if not should_reject_address(addr):
        return {
          'address': '{0} {1}'.format(addr, DEFAULT_CITY),
          'source': 'Source Not Set',
          'type': 'route'
        }      
    
    # No dice.
    return None
  
  # Returns the distance in feett from the northeast corner to the southwest corner of a bounded region.
  # We use this to detect
  def getDistanceOfBoundingArea(self, bounds):
    northeast = bounds['northeast']
    southwest = bounds['southwest']
    return LatLonDistance(northeast["lat"], northeast["lng"], southwest["lat"], southwest["lng"]) * 5280
  
  def _getLatLonFromGeocode(self, geocode, data):
    for result in geocode['results']:
      # data['type'] is something like 'address' or 'intersection'.
      if data['type'] in result['types']:
        loc = result['geometry']['location']
        if data['type'] == 'route': # No exact street address, just a road name.
          # Is the area enclosing the road too large?  If it's above a certain threshold than the street
          # is too long and it wouldn't make sense to show a photo in the middle of it
          boundLengthInFt = self.getDistanceOfBoundingArea(result['geometry']['bounds'])
          if boundLengthInFt > MAX_BOUND_SIZE:
            return None
        return (loc['lat'], loc['lng'])

  def getLatLonFromGeocode(self, geocode, data, r):
    latlon = self._getLatLonFromGeocode(geocode, data)
    if not latlon:
      return None
    return latlon
  
  def finalize(self):
    pass

  def name(self):
    return 'free-streets-boston'


coders.registration.registerCoderClass(FreeStreetBostonCoder)
