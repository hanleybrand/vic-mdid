from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
import uuid
import logging


class Viewer(object):

    embed_template = 'viewers_embed.html'
    is_embeddable = False
    default_options = dict()

    def __init__(self, obj, user, options=None):
        self.user = user
        self.obj = obj
        self.options = options

    def url(self, urltype='shell'):
        kwargs = {
            'viewer': self.name,
            'objid': self.obj.id,
        }
        return reverse('viewers-viewer-%s' % urltype, kwargs=kwargs)

    def embed_code(self, request, options):
        if not self.is_embeddable:
            return None
        return render_to_string(self.embed_template,
                                {
                                    'viewer': self,
                                    'divid': 'v' + str(uuid.uuid4())[-12:],
                                    'obj': self.obj,
                                    'options': options,
                                    'request': request,
                                    'url': self.url('script'),
                                })

    def get_options_form(self):
        return None

    def embed_script(self, request):
        return None

    def view(self, request):
        return None



_registered_viewers = dict()

def discover_viewers():
    print 'registered viewers are: '
    print _registered_viewers
    if not _registered_viewers.has_key("__REGISTRATION_COMPLETED__"):
        _registered_viewers["__REGISTRATION_COMPLETED__"] = lambda obj, request: None
        print 'apps are: '
        for app in settings.INSTALLED_APPS:
            try:
                logging.debug("Checking for viewers in %s.viewers" % app)
                print ' i am trying to import: '+app
                __import__(app + ".viewers")
                print ' i may have successfully imported: '+ app
            except ImportError, ex:
                logging.error("Failed to import viewers: %s" % ex)
                print ex
                pass


def get_registered_viewers():
    discover_viewers()
    print 'discovered viewers: ' + str(_registered_viewers)
    return _registered_viewers


def register_viewer(name, cls):
    def register(func):
        _registered_viewers[name] = func
        logging.debug("Successfully registered viewer %s" % name)
        setattr(cls, 'name', name)
        return func
    return register


def get_viewers_for_object(obj, request):
    viewers = []
    viewer_list = get_registered_viewers()
    for viewer in viewer_list.values():
        v=viewer(obj, request)
        if v: 
            viewers.append(v) 
    #return (viewer for viewer in viewers if viewer)
    return viewers

def get_viewer_by_name(viewer_name):
    return get_registered_viewers().get(viewer_name)
