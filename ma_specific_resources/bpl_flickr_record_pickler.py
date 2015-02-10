'''
  Downloads image date from a flickr collection, parses records and then pickles them.  This is currently targeted to the format used by the
  Charlestown lantern collection by BPL.  It will be expanded
'''
import flickrapi, json, re, HTMLParser, record, cPickle

html_parser = HTMLParser.HTMLParser()
flickr_private_info = open("flickr_private_info.txt") # Files containing my flickr API and private key, not checked into to source control.
API_KEY = flickr_private_info.readline().split()[1]
SECRET = flickr_private_info.readline().split()[1]
BPL_FLICKR_NAME = 'boston_public_library'
FLICKR_BASE_URL = 'https://www.flickr.com/photos/'

# See https://www.flickr.com/services/api/misc.urls.html for a description of the URLs below
FLICKR_IMAGE_URL = 'http://farm{farm}.staticflickr.com/{server}/{id}_{secret}_b.jpg'
FLICKR_IMAGE_THUMBNAIL_URL = 'http://farm{farm}.staticflickr.com/{server}/{id}_{secret}_n.jpg'
flickr = flickrapi.FlickrAPI(API_KEY, SECRET)
#photos = flickr.photos_search(user_id = libary_user_id, per_page='10')
#sets = flickr.photosets_getList(user_id = libary_user_id)
#libary_user_id = '73509078@N00'

# Defines albums who's photos we want to iterate through.
album_sets = [{
               'name': 'Charlestown Lantern Slides',
               'id': '72157622473902447'
              }]

# Our regexes are based on the photos' metadata in the charlestown collection here:
# https://www.flickr.com/photos/boston_public_library/sets/72157622473902447
def parse_record_from_charleston_lanterns(album, photo_id):
  r = record.Record()
  photo_as_json = flickr.photos_getInfo(photo_id = photo_id, format="json")
  photo_obj = json.loads(photo_as_json.replace("jsonFlickrApi(", "")[:-1])["photo"]
  photo_info = photo_obj["description"]["_content"]
  
  r.photo_url = FLICKR_IMAGE_URL.format(farm = photo_obj["farm"],
                                        server = photo_obj["server"],
                                        id = photo_id,
                                        secret = photo_obj["secret"])
  r.thumbnail_url = FLICKR_IMAGE_THUMBNAIL_URL.format(farm = photo_obj["farm"],
                                           server = photo_obj["server"],
                                           id = photo_id,
                                           secret = photo_obj["secret"])
  r.preferred_url = [FLICKR_BASE_URL + BPL_FLICKR_NAME + "/" + photo_id + "/in/set-" + album["id"]]
  r.tabular = {
               'l': r.preferred_url, # Not the real address
               'i': [photo_id],
               'p': [html_parser.unescape(re.search(r".*Creation date:[ ]*</b>(.+?)(?=\n+<b>Description)", photo_info, re.DOTALL).group(1))], # date
               'r': [html_parser.unescape(re.search(r".*Description:[ ]*</b>(.+?)(?=\n+<b>Genre)", photo_info, re.DOTALL).group(1))],  # description
               't': [html_parser.unescape(re.search(r".*Title:[ ]*</b>(.+?)(?=\n+<b>Creation date)", photo_info, re.DOTALL).group(1))], # title
               'n': '', #Notes
               'a': [album["name"]]
               }
  return r

# Writes them out in a pickled format that the generate-geocodes.py file can read
def pickle_records(records):
  output_file = "boston_records.pickle"
  pickler = cPickle.Pickler(file(output_file, "w"), 2)
  for record in records:
    pickler.dump(record)

if __name__ == '__main__':
  records = []
  for photo in flickr.walk_set(album_sets[0]["id"], per_page=200):
    photo_id = photo.get("id")
    try:
      newRecord = parse_record_from_charleston_lanterns(album_sets[0], photo_id)
      records.append(newRecord)
      print ("{0}: Loaded {0} with id: {1}".format(len(records), newRecord.title(), newRecord.photo_id()))
    except Exception as e:
      print("Failed to extract data for photo with id: {0}\n Error was: {1}".format(photo_id, e))
  pickle_records(records)
  print("Picked {0} images".format(len(records)))