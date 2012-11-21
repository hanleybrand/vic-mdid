from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
import re 
import json

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
"""
def break_query_string(query):
    print "NGA breaking query"
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
  
    return keywords, para_map
    
    
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
  
  
def check_Empty(paramlist):
   if len(paramlist.keys()) == 0:
     return true
   else:
    for parameter in paramlist:
	return false