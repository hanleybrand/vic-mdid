import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser
#from rooibos.settings_local import TROVE_KEY
from rooibos.unitedsearch import *              # other search tools
from rooibos.unitedsearch.common import *   # methods common to all databases
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures

name = "Trove"
identifier = "trove"

TROVE_URL = "http://trove.nla.gov.au"
BASE_URL = "http://trove.nla.gov.au/picture/result?"
API_URL = "http://api.trove.nla.gov.au/result?key=TROVE_KEY&zone=picture&q="
BASE_SEARCH_URL = "http://trove.nla.gov.au/picture/result?FIELDSDATEFORMAT&s=OFFSET"
PER_PAGE = 20 #how many results trove actually has per page - can't change this

"""
TODO: DELETE THE API KEY AFTER DEVELOPMENT,
get a key associated with the university
"""
TROVE_KEY = "ot2eubi7h2ef5qjn"
api = False
"""API technical docs:
http://trove.nla.gov.au/general/api-technical
"""
def count(query) :
    url = build_URL(query)
    search_result_parser = get_search_result_parser(url, 0)
    #return 12345
    return _count(search_result_parser)

def _count(soup):
    num=0
    #TODO: api or html
    if api:
        result = soup.find("records")["total"]
        num = int(result)
    else:
        result = soup.find("div", attrs={'id':"pictures"}).find("div", attrs={'class':"hdrresult"}).find("strong")
        num = int(re.sub("[^0-9]+", "", result.text))
    print "trove.py, _count, number of results string: "+str(num)
    return num


    
def search(query, params, off, num_wanted) :
    print "params in trove"
    print params
    url = build_URL(query)
    print "trove.py, search, url = "+url
    search_result_parser = get_search_result_parser(url, off)
    print "trove.py, search, has search_result_parser: "+str(search_result_parser is not None)

    #TODO: api or html
    if api:
        images = parse_api_results(search_result_parser)
    else:
        images = parse_results(search_result_parser)

    img_list = Result(_count(search_result_parser), int(off)+PER_PAGE)
    for image in images:
        img_list.addImage(ResultImage(image[0], image[1], image[2], image[3]))
    return img_list, empty_params
    #return Result(0, off), empty_params

    
def parse_api_results(soup):
    images = []
    works = soup.findAll("work")
    for work in works:
        id = work["id"]
        thumb=""
        thumbId = work.find("identifier", attrs={'linktype':'thumbnail'})
        if thumbId:
            thumb = thumbId.text
        image = get_image_from_thumb(thumb)
        desc = ""
        descId = work.find("title")
        if descId:
            desc = descId.text
        descId = work.find("contributor")
        if descId and desc in "":
            desc += "\n"+descId.text
        descId = work.find("troveurl")
        if descId and desc in "":
            desc += "\n"+descId.text
        data={'image':image, 'thumb':thumb, 'desc':desc, 'troveid':str(id)}
        if thumb is not "":
            images.append([image, thumb, desc, json.dumps(data)])
    return images

    #TODO: api or html
def parse_results(soup):
    results = soup.findAll("li", attrs={'class':re.compile("draggableResult")}, limit=20) #results double up after 20
    images = []
    num_loaded = 0
    debug = False
    for result in results:
        #print result.prettify()
        
        #"""
        title_block = result.find("dt")
        if title_block:
            title = title_block.text
        else:
            title=""#where else can we find the title?
        description = title_block.find("a")['href']
        id = int(re.findall("[0-9]+", description)[0]) if description else 0
        if debug : print "Image id = "+str(id)
        creator = result.find("dd", attrs={'class' : "creator"})
        kw = result.find("dd", attrs={'class' : "keywords"})
        online = result.find("dd", attrs={'class' : "online singleholding"})
        thumbdd = result.find("dd", attrs={'class' : "thumbnail"})
        thumba = thumbdd.find("a") if thumbdd else None
        thumbimg = thumba.find("img") if thumba else None
        thumb = thumbimg['src'] if thumbimg else ""
        #"""
        desc = title if title else kw.text
        image = get_image_from_thumb(thumb)
        data={'image':image, 'thumb':thumb, 'desc':desc, 'troveid':str(id)}
        if thumb:
            #images.append([TROVE_URL+description if description else get_image_from_thumb(thumb), thumb, kw.text if kw else title, str(id)])
            images.append([image, thumb, desc, json.dumps(data)])
            num_loaded += 1
    print "trove.py, search, found a page with "+str(len(images))+" results"
    return images

def get_image_from_thumb(thumb):
    url = thumb.replace("_t.", ".")
    if "quod.lib.umich.edu" in url:
        arts = re.findall("[^_]+", re.findall("[^jpg]+", re.findall("[^/]*.jpg", url)[0])[0].strip('.'))
        if arts and len(arts) is 2:
            return "http://quod.lib.umich.edu/cgi/i/image/getimage-idx?viewid="+arts[0]+"_"+arts[1]+".JPG;cc=musart;entryid=x-"+arts[0]+"-SL-"+arts[1]+";quality=m800;view=image"
    url = url.replace("/SML/", "/LRG/")
    url = url.replace("_DAMt", "_DAMl").replace("t.jpg", "r.jpg")
    url = url.replace(".JPG.jpg", ".JPG")
    url = url.replace("/thum/", "/full/").replace("s.jpg", ".jpg")
    if "thumbnail.exe" in url:
        url = url.replace("thumbnail.exe", "getimage.exe") + "&DMSCALE=0&DMWIDTH=0"
    url = url.replace("/thumbnail/", "/reference/")

    """
    http://quod.lib.umich.edu/m/musart/thumb/1/2/5/1958_1.125.jpg
    turns to
    http://quod.lib.umich.edu/cgi/i/image/getimage-idx?viewid=1958_1.125.JPG;cc=musart;entryid=x-1958-SL-1.125;quality=m800;view=image
    important bit is 1958_1.125
    http://content.cdlib.org/ark:/13030/kt3v19r78d/thumbnail
    no idea what to turn it into, main page:
    http://content.cdlib.org/ark:/13030/kt3v19r78d/
    """
    
    return url
def build_URL(query):
    print "trove.py, build_URL( "+query+" )"
    fields_string=""
    fields = {}
    year_from = year_to = None
    keywords, para_map = break_query_string(query)
    print "trove.py, build_URL, query = "+query
    print "trove.py, build_URL, keywords = "+keywords
    print "trove.py, build_URL, para_map = "+str(para_map)
    #params, unsupported_parameters = merge_dictionaries(para_map, params, valid_keys)
    for key in para_map.keys():
        print "trove.py, build_URL, for key in para_map.keys loop, key = "+key+", value = "+para_map[key]
        if key in "start_date":
            print "trove.py, build_URL, start date found, and is "+para_map[key]
            year_from = int(para_map[key])
            del(para_map[key])
        elif key in "end_date":
            print "trove.py, build_URL, end date found, and is "+para_map[key]
            year_to = int(para_map[key])
            del(para_map[key])
        else:
            param = get_param(key)#if key is valid(or synonym) param is it's correct name for trove, otherwise key is unsupported and param is "" (keyword)
            if param is "":#key unsupported
                keywords += " "+para_map[key]
            else:
                fields[param] = para_map[key]# fields will now contain all supported parameters and their values
    if api:
        url = API_URL.replace("TROVE_KEY", TROVE_KEY)
        if keywords:
            url += keywords.strip().replace(" ", "+").replace("++", "+")
        for key in fields.keys():
            val = fields[key]
            if " " in val or "+" in val:
                val = "\""+val+"\""
            url += "+"+key+'%3A'+val.replace(" ", "+").replace("++", "+")
        url += build_date(year_from, year_to)
        return url

    else:
        id=0
        if keywords:
            fields_string += build_field(id, "", "all", keywords.strip().replace(" ", "+").replace("++", "+"))
            id += 1
        for key in fields.keys():
            fields_string += build_field(id, key, "all", fields[key])
            id+=1

        url = BASE_SEARCH_URL.replace("FIELDS", fields_string)
        url = url.replace("DATE", build_date(year_from, year_to))
        url = url.replace("FORMAT", "")
    return url
    

def build_field(id, field, f_type, term):
    print "trove.py, build_field("+str(id)+", "+field+", "+f_type+", "+term+")"
    amp = ""
    if id > 0:
        amp = "&"
    if field is "all words":
        field = ""
    if field and field is not "":
        field = field + "%3A"
    return amp+"q-field"+str(id)+"="+field+"&q-type"+str(id)+"="+f_type+"&q-term"+str(id)+"="+term

def build_date(year_from, year_to):
    print "trove.py, build_date("+str(year_from)+", "+str(year_to)+")"
    if not year_from:
        if not year_to:
            return "" #no date entered
        return "" # let's not bother with those who don't enter start year TODO: maybe we can auto set start since end is actually set
    if not year_to: #start year is set, but not end year
        year_to = 3000
    if api:
        return "date:["+str(year_from)+"+TO+"+str(year_to)+"]"
    return "&q-year1-date="+str(year_from)+"&q-year2-date="+str(year_to)
        
"""
Feed an assembled url into here, with the offset, and get a parser for 20 results
"""
def get_search_result_parser(base_url, offset) :
    page_url = re.sub("OFFSET", str(offset),base_url)
    #page_url = "http://api.trove.nla.gov.au/result?key="+TROVE_KEY+"&zone=picture&q=cat"
    print "trove.py, get_search_result_parser, page_url = "+page_url

    #TODO: replace this with a WORKING html library retrieval
    if api:
        f = open("/u/students/novikovech/mdidtestpages/result.xml")
    else:
        f = open("/u/students/wangrui1/trove/result.html")
    html = ""
    for line in f:
        html += line

    #html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(page_url)
    #print html
    search_results_parser = BeautifulSoup(html)
    print "trove.py, get_search_result_parser returns  a soup: "+str(search_results_parser is not None)
    return search_results_parser








"""
Required, accessed by external method to select images
"""
def getImage(datastring):
    print datastring.__class__
    data = json.loads(datastring) if isinstance(datastring, unicode) or isinstance(datastring, str) else datastring
    print "get image from : "+str(data)
    thumb = data.get("thumb")
    image = data["image"]
    desc = data["desc"]
    print "got all data"
    meta = {'creator':'somebody'}#use data['troveid'] to find the metadata using the api?
    i = RecordImage(image, thumb, desc, meta, json.dumps(data))
    print "img = "+str(i)
    #img = RecordImage(url, thumb, name, meta, identifier)
    #print "Constructed image: "+str(img)
    return i







"""
Check if given param is valid or under different name(creator=artist, etc), return as empty param (keyword) if not
"""
def get_param(param):
    if param in synonyms.keys():
        return synonyms[param]
    return ""


field_types = ["keyword","creator", "title", "subject","isbn","issn","public tag"]
option_types = ["all of the words", "any of the words", "the phrase", "none of the words"]   
    
"""
PARAMMAP
"""
parameters = MapParameter({
    "start year": OptionalParameter(ScalarParameter(str)),
    "end year": OptionalParameter(ScalarParameter(str)),
    "availability": DefinedListParameter(["All", "Online", "Access conditions", "Freely available", "Unknown"],  multipleAllowed=False, label="Availability"),
    "language": DefinedListParameter(["All", "French", "English", "Italian", "Chinese", "Spanish", "German", "Greek", "Latin"],  multipleAllowed=False, label="Language"),
    "field" : ListParameter([
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        )
        ],label="Keywords")
    })

    
    
valid_keys = empty_params = {"all words": [],
    "exact phrase": [],
    "exclude words": [],
    "creator": [],
    "title": [],
    "subject": [],
    "isbn": [],
    "issn": [],
    "publictag": [],
    "access": [],
    "start year": [],
    "end year": [],
    "availability":[],
    "language":[],
    "field" :[]
    }

synonyms = {"all words": "",
    "creator" : "creator",
    "author" : "creator",
    "artist" : "creator",
    "photographer" : "creator",
    "painter" : "creator",
    "title" : "title",
    "subject" : "subject",
    "isbn" : "isbn",
    "issn" : "issn",
    "tag" : "publictag",
    "publictag" : "publictag",
    "access" : "access",
    "copyright" : "access",
    }