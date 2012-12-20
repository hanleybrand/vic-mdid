""" National Gallery of Australia"""
from rooibos.unitedsearch import *		# other search tools, such as parameter types
from rooibos.unitedsearch.common import *	# methods common to all external searchers
import urllib2					# to get page from url address
from BeautifulSoup import BeautifulSoup		# html scraper
from rooibos.unitedsearch.external.translator.query_language import Query_Language					# reads query into usable form
from rooibos.unitedsearch.external.ngaust_parser import parse_parameters				# reads params from sidebar


name="National Gallery of Australia"
identifier = "ngaust"
LOGO_URL = "http://nga.gov.au/common/graphics/NGA-INLINE-SPLICE-LTGREY.png"
HOMEPAGE_URL = "http://nga.gov.au/Home/Default.cfm"

# use simple search for search by keyword
# note, VIEW_SELECT=2 means show images and captions, order_select is whether to order by title, author, date, etc
ADVANCED_SEARCH_BASE_URL = "http://artsearch.nga.gov.au/Search.cfm?mystartrow=OFFSET&realstartrow=OFFSET&VIEW_SELECT=2&PARAMETERS&order_select=ORDER_TYPE_INT&showrows=NUM_IMAGES"
SIMPLE_SEARCH_URL_STRUCTURE = "http://artsearch.nga.gov.au/Search.cfm?mystartrow=OFFSET&realstartrow=OFFSET&srchmeth=1&order_select=ORDER_TYPE_INT&view_select=2&showrows=NUM_IMAGES&simple_select=1&keyword=VALUE"

order_values = ["Artist", "Date", "Title", "Birth Date", "Accn Number", "Media", "Technique", "Impression", "Imaged"]
url_replacement_types = {"artist": "aname", "start": "yeara", "end": "yearb", "publisher": "pub"}
	# url replacements for when url value is different to param name in parameters (ie, non-default)
			

def search(query, params, offset, num_wanted):

    offset = int(offset)    
    # get query terms in usable form (expect one of query or params
    if query and not params:
	query_terms = Query_Language(identifier).searcher_translator(query)
    elif params and not query:
	query_terms = parse_parameters(params)
    elif not params and not query:
	print "shouldn't ever end up here...Ngaust has both query (%s) and params (%s)" %(query, params)
	raise NotImplementedError
    else:
	return Result(0, off), build_empty_params()
	
    
    # get 1st page
    url_base = _get_url(query_terms)
    html_page = _get_html(url_base, offset, num_wanted)
    scraper = BeautifulSoup(html_page)
    total = _count(scraper)

    # deal with there being fewer images than desired
    if total < offset:
	return Result(0, offset), {}
    if total < num_wanted:
	num_wanted = total
	result = Result(total, offset+total)	# TODO, what offset should this actually return?
    else:
	result = Result(total, offset+num_wanted)


    """
    # get actual images and add to result
    first_loop = True
    num_images = 0
    while num_wanted > 0:
	
	if not first_loop:	# optimisation so we don't have to get the first page twice
	    scraper = BeautifulSoup(_get_html(url_base, offset+num_images, num_wanted))
	images = _get_images(scraper, num_wanted)
	for image in images:
	    result.addImage(image)
	num_wanted -= len(images)
	num_images += len(images)
	first_loop = False
    """
    images = _get_images(scraper, num_wanted)
    for image in images:
	result.addImage(image)
    
    """
    empty_params = build_empty_params(parameters)
    params = merge_dictionaries(empty_params, params, parameters.parammap.keys())[0]
    """
    returning_params = _build_returnable_parameters(query_terms)

    return result, returning_params
    
    #print "NGaust search"
    #return Result(0, 0), build_empty_params(parameters)
    
def count(query):
    query_dict = Query_Language(identifier).searcher_translator(query)
    url_base = _get_url(query_dict)
    scraper = BeautifulSoup(_get_html(url_base, 0, 1))
    
    return _count(scraper)


def getImage(json_image_identifier):

    image_identifier = json.loads(json_image_identifier)
    # get any wanted values out of image_identifier, and leave all others to form the meta dict
    url = image_identifier.pop('url')
    thumb = image_identifier.pop('thumb')
    title = image_identifier.pop('title')
    
    return Image(url, thumb, title, image_identifier, json_image_identifier)


def _get_url(query_dict):
    
    if 'All Words' in query_dict:
	# simple search (can't do both at once, so have to shove advanced parameters into keywords)
	
	keyword_string = ""
	for para in query_dict:
	    if not para is 'display_order':	# special case, as this parameter is still available in simple search
		keyword_string += query_dict[para] + " "
	url_base = SIMPLE_SEARCH_URL_STRUCTURE.replace('VALUE', keyword_string)
	query_dict = {
	    "All Words": keyword_string,
	    "display_order": query_dict.get('display_order' or 'Artist')
	}
			
    else:
	# advanced search
	params_string = ""
	for para in query_dict:
	    if not para is 'display_order':
		url_term = url_replacement_types[para] if para in url_replacement_types else para
		if not len(query_dict[para]) is 0:
		    params_string += "&" + url_term + "=" + query_dict[para]
		
	# remove leading '&'
	params_string = params_string.rstrip('&')
	
	url_base = ADVANCED_SEARCH_BASE_URL.replace('PARAMETERS', params_string)

    # set display order
    if 'display_order' in query_dict and not query_dict['display_order'] is None:
	order_choice = query_dict["display_order"].title()
    else:
	order_choice = 'Artist'

    if order_choice in order_values:	# valid choice
	order_int = str(order_values.index(order_choice)+1)	# +1 because ngaust counts from 1, not 0
    else:
	order_int = "1"
    url_base = url_base.replace('ORDER_TYPE_INT', order_int)
    
    return url_base
		
    """ Old version from pre query language
    keywords, para_map = break_query_string(query)
    params, unsupported_parameters = merge_dictionaries(para_map, params, parameters.parammap.keys())
    if not keywords is u'':	# have keywords to add
	add_to_dict(params, "All Words", keywords)
    
    if not params.has_key('All Words'):
	# advanced search
	param_string = ""
	for param in params:
	    url_term = url_replacement_types[param] if param in url_replacement_types else param
	    url_value = " ".join(params[param])
	    if not len(url_value) is 0:
		param_string += "&" + url_term + "=" + url_value
	    
	    # have made parameters string, now remove leading &
	    param_string = param_string[1:]
	    
	url_base = ADVANCED_SEARCH_BASE_URL.replace("PARAMETERS", param_string)
	
    else:
	# simple search, shove all parameters into keywords
	remaining_params = {}
	if params.has_key('All Words'):
	    remaining_params['All Words'] = params['All Words']
	    del(params['All Words'])
	else:
	    remaining_params['All Words'] = []
	
	if params.has_key('display_order'):
	    remaining_params['display_order'] = params['display_order']
	    del(params['display_order'])
	else:
	    remaining_params['display_order'] = ["Artist"]	# default
	    
	for param in params:
	    add_to_dict(remaining_params, "All Words", params[param])
	
	url_base = SIMPLE_SEARCH_URL_STRUCTURE.replace("VALUE", remaining_params["All Words"][0])
	params = remaining_params
	
    # and set order
    
    order_choice = params["display_order"][0].title() if params.has_key('display_order') else 'Artist'
    if order_choice in order_values:
	url_base = url_base.replace("ORDER_TYPE_INT", str(order_values.index(order_choice)+1))	# +1 because ngaust counts from 1, not 0
    else:
	url_base = url_base.replace("ORDER_TYPE_INT", "1")	# default
	
    return url_base
    """
    
def _get_html(url_base, offset, num_wanted):
    
    url = url_base.replace("OFFSET", str(offset+1)).replace("NUM_IMAGES", str(num_wanted))	# image to start at. NGaust is 1-indexed
    print "NGaust url: %s" %url
    opener = proxy_opener()
    try:
	html = opener.open(urllib2.Request(url))
	return html
    except urllib2.URLError:
	return None
    
    
def _count(scraper):
    
    #print "NGaust l118 scraper %s" %(scraper)
    #print "NGaust l119 count_tag %s" %(scraper.find('div', 'PAGIN'))
    count_tag = scraper.find('div', 'PAGIN')
    print "NGaust scraper: %s\n\n" %scraper
    if count_tag:
	return int(count_tag.b.contents[0])
    # else, maybe was an invalid search term
    else:
	return 0
    
   

def _get_images(scraper, num_wanted):
    
    images = []
    
    image_divs = scraper.find("ul", id="GRID").findAll("li", limit=num_wanted)
    
    for image_div in image_divs:
	image_tag = image_div.find("img")
	thumb_url = "http://artsearch.nga.gov.au/" + image_tag['src']
	image_url = thumb_url.replace("SML", "LRG")
	
	caption_tag = image_div.find('div', 'GRIDCAPTION')
	artist_tag = caption_tag.find('p', 'ARTIST')
	if artist_tag.span.contents:
	    artist = artist_tag.span.contents[0] + artist_tag.span.nextSibling
	else:
	    artist=""
	#artist = "%s %s" %(artist_tag.span.contents, artist_tag.span.nextSibling)	# artist last name + first name
	
	artist_date_tag = caption_tag.find('p', 'ARTISTDATE')
	artist_date = artist_date_tag.contents
	
	link_tag = artist_date_tag.findNextSibling('p')
	more_info = "http://artsearch.nga.gov.au/%s" %(link_tag.a["href"])
	title = link_tag.a["title"]
	other = link_tag.a.nextSibling	# date, medium, etc
	
	description = image_tag['alt']
	image_identifier = {"thumb": thumb_url,
			    "url": image_url,
			    "description": description,
			    "artist": artist,
			    "more_info": more_info,
			    "title": title,
			    "other": other}		# TODO Check scraping the caption doesn't take too long
	images.append(ResultImage(image_url, thumb_url, description, json.dumps(image_identifier)))
	
    return images


def build_empty_params(mapParameter):
    empty = {}
    for param in mapParameter.parammap.keys():
	empty[param] = []
    return empty


def _build_returnable_parameters(params):
    returnables = {}
    for key in params:
	if isinstance(params[key], list):
	    returnables[key] = params[key]
	else:
	    returnables[key] = [params[key]]
    
    for unused_key in (set(parameters.parammap)-set(params)):
	returnables[unused_key] = []
	
    return returnables
    
    
parameters = MapParameter({
    "artist": OptionalParameter(ScalarParameter(str), "Artist"),
    "title": OptionalParameter(ScalarParameter(str), "Title"),
    "display_order": DefinedListParameter(order_values, label="Display Order"),
    "date": OptionalParameter(ScalarParameter(str), "Date"),
    "medium": OptionalParameter(ScalarParameter(str), "Medium"),
    "birthdate": OptionalParameter(ScalarParameter(int), "Birth"),
    "deathdate": OptionalParameter(ScalarParameter(int), "Death"),
    "placemade": OptionalParameter(ScalarParameter(str), "Place Made"),
    "pubplace": OptionalParameter(ScalarParameter(str), "Place Published"),
    "publisher": OptionalParameter(ScalarParameter(str), "Publisher"),
    "technique": OptionalParameter(ScalarParameter(str), "Technique"),
    "accno": OptionalParameter(ScalarParameter(str), "Accn Number")
    })

def get_logo():
    return LOGO_URL
    
def get_searcher_page():
    return HOMEPAGE_URL