from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
import re 
import json


API_KEY="sfypBYD5Jpu1XqYBipX8"

""" Methods for all UnitedSearch searchers """
def get_collection():
	collection, created = Collection.objects.get_or_create(
		name='unitedsearch',
		defaults={
			'title': 'United Search collection',
			'hidden': True,
			'description': 'Collection for images retrieved through the United Search'
		})
	if created:
		authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
		AccessControl.objects.create(content_object=collection, usergroup=authenticated_users, read=True)
	return collection


def get_storage():
	storage, created = Storage.objects.get_or_create(
		name='unitedsearch',
		defaults={
			'title': 'United Search collection',
			'system': 'local',
			'base': os.path.join(settings.AUTO_STORAGE_DIR, 'unitedsearch')
		})
	if created:
		authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
		AccessControl.objects.create(content_object=storage, usergroup=authenticated_users, read=True)
	return storage
	
	
#METHODS FOR EXTERNAL DATABASES =====================

"""
Breaks query string into parameters and keywords 
query is in form search=search_type, keywords=words (space-separated), params={"type": "value", ...}
or form word
"""
def break_query_string(query):
    keywords = ""
    para_map = {}

    
    keywords = re.findall("(?<=keywords=)[^,]*", query) # here keywords contains a list

    if keywords and len(keywords) >= 1:
        keywords = keywords[0] #now keywords is a string from that list.
    else:
        keywords=""
      
    para_map = re.findall("(?<=params=).*", query)
    if para_map and len(para_map) >= 1:
        para_map = json.loads(para_map[0])
    else:
        para_map = {}
  
    # default, if query didn't follow search=... structure, simply use query itself
    print "common:"
    print keywords
    print para_map
    if keywords is "" and len(para_map) is 0 :
	print "in if, keywords:"
	keywords = query or ""
	print keywords
	print "\n\n"
    return keywords, para_map
    
#========Dictionary methods ========

def merge_dictionaries(dict1, dict2, valid_keys):
    # note, have to put all values into dict2 in order for views.py to remember defaults. Assume all keys in dict2 are valid, as generated by program, not user
    
    unsupported_parameters = {}
    """
    print "dic 1 and dic2"
    print dict1
    print dict2
    """
    for key in dict1:
      newKey = key

      print newKey
      if newKey in valid_keys:	# all types of parameter defined for this class
	# supported parameter type
	add_to_dict(dict2, newKey, dict1[key])
      else :
	# unsupported, so add to list of errors, and treat value as a keyword
	add_to_dict(unsupported_parameters, key, dict1[key])
	add_to_dict(dict2, "All Words", dict1[key])
    return dict2, unsupported_parameters
    
#checks if key and value exist in dict and adds them
def add_to_dict(dictionary, key, value):
  
    if isinstance(value, list):
      if len(value) == 0:	# if empty list, make sure entry exists anyway
	if not key in dictionary:
	  dictionary[key] = []
      for v in value:
	add_to_dict(dictionary, key, v)
    else:
      if key in dictionary:
	  if value not in dictionary[key]:
	      dictionary[key].append(value)
      else:
	  dictionary[key] = [value]	# want final result to be in a list
  
  
# return either the value at 0 in the dictionary argument, or "" if none exists
def getValue(dictionary, key):
  # check if key exists
  # else set to ""
  if key in dictionary:
     value = dictionary[key]
     if isinstance(value, list):
	value_string = ""
	for li in value:
	  value_string += li+" "
	value = value_string.strip()
  else:
    value = ""
  return value
  

synonyms_lists = [["artist","author","painter"],
	    ["subject","keyword","all","all words"]]
	    
# return a supported synonym of key if one exists, or None
def get_supported_synonym(key, valid_keys):
  
  for syn_list in synonyms_lists:
    if key.lower() in syn_list:
      # find synonmym for key which works for valid_keys as well
      valid_syns = list(set(syn_list) & set(valid_keys))
      
      if len(valid_syns) > 0:
	# found (at least) a match!
	return valid_syns[0]
      else:	# assumes no two synonyms lists are overlapping. If any do, change this
	return None
  
#=============Helper Methods ============
""" Example desired format: ddmmyyyy
	Can have no days, and/or no months, and 2 or 4 year-specifiers
    Example separators: "", ".", "/", "-", None
    
    Will return "" if date is unparsable or invalid

    Supported incoming formats: "ddmmyy[yy]", "dd-mm-yy[yy]" (or any non-numeric separator), "mm-yy[yy]", "yy[yy]", None, ""
	Passing None or "" as date returns current date
	If no day or month is specified, returns jan 1st
	Note, doesn't support BC dates, or specification of BC, AD

    If month or day is invalid (eg, mm = 21), attempts swapping month and day order
"""
def format_date(date, format, separator):

  if isinstance(date, str) or isinstance(date, unicode):
    # break down string into parts

    # first, check if date is just a year:
    year_match = re.match("^(\d{2,4})$", date)
    if year_match:
      day_int = 1
      month_int = 1
      year_int = int(year_match.group(0))
      # then, try matching full date
    else:
      date_match = ("^(?P<day>(\d{0,2}))(?P<separator>\D?)(?P<month>(\d{0,2}))((?P=separator)|\D)(?P<year>(\d{2,4}))$", date)
      if date_match:
	day = date_match.group("day")
	month = date_match.group("month")
	year = date_match.group("year")
	  
	# regex always matches day over year if one is present, and we want to treat it as month
	if day and not month:
	  month = day
	  day = "01"
	  
	day_int = int(day) if day else 1
	month_int = int(month) if day else 1
	year_int = int(year)

    # format date
    # validate date (simple validation, eg assume 31 feb is valid)
    if day_int < 0 or day_int > 31:
	# invalid
	return ""







