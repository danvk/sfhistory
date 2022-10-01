#!/usr/bin/env python3
"""Generates by-location JSON files ala OldNYC.

See https://github.com/danvk/oldnyc/blob/a09ea03e8b0f96ffe235755a1120569a61a0dd79/generate_static_site.py#L178
"""

from collections import OrderedDict
import csv
import json

records = json.load(open('records.js'))
print('Loaded', len(records), 'records from JS file.')  # Loaded 38637 records from JS file.
id_to_record = {r['id']: r for r in records}

# strip leading 'var lat_lons = ' and trailing ';'
lat_lons_js = json.loads(open('lat-lons.js', 'rb').read()[15:-2])
lat_lon_to_ids = {
    latlng: [photo_id for _y1, _y2, photo_id in photos]
    for latlng, photos in lat_lons_js.items()
}
photo_id_to_year = {}
for photos in lat_lons_js.values():
    for y1, y2, photo_id in photos:
        photo_id_to_year[photo_id] = [y1, y2]

print('Have', len(lat_lon_to_ids), 'distinct lat/lngs')  # Have 2133 distinct lat/lngs

photo_id_to_size = {
    photo_id: (int(width), int(height))
    for photo_id, width, height in csv.reader(open('../image-sizes.txt'))
}

def make_response(photo_ids):
    response = OrderedDict()
    for photo_id in photo_ids:
        r = id_to_record[photo_id]
        width, height = photo_id_to_size[photo_id]

        response[photo_id] = {
          'title': r['title'],
          'date': r['date'],
          'years': photo_id_to_year[photo_id],
          'folder': r['folder'],
          'library_url': r['url'],
          'width': width,
          'height': height,
        }

    # Sort by earliest date; undated photos go to the back.
    ids = sorted(photo_ids, key=lambda id: min(response[id]['years']) or 'z')
    return OrderedDict((id_, response[id_]) for id_ in ids)


for latlon, photo_ids in lat_lon_to_ids.items():
    if 'egg' in photo_ids:
        continue
    outfile = 'by-location/%s.json' % latlon.replace(',', '')
    response = make_response(photo_ids)
    json.dump(response, open(outfile, 'w'), indent=2)
