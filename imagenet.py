#!/usr/bin/python
import urllib
import urllib2
import simplejson
from functools import partial

import numpy

import weby
from weby.templates.helpers import html

app = weby.defaults.App()

def image_urls_for_synset(wnid):
    if wnid.startswith('n'):
        base_url = 'http://www.image-net.org/api/text/imagenet.synset.geturls?wnid=%s'
        url = base_url % wnid
        urls = [u for u in urllib2.urlopen(url).read().split('\n') if u.startswith('http')]
        numpy.random.shuffle(urls)
        return urls
    else:
        return []
    
@app.subapp('images')
@weby.urlable_page()
def images(req, page):
    synset_id = req.params.get('synset', None)
    if synset_id is not None:
        wnid = wordnet_ws('synset_pos_offset', {'synset':synset_id})
        images = image_urls_for_synset(wnid)
    else:
        images = []
    page(unicode(simplejson.dumps(images[0:4])))

def web_service(url, path, attrs):
    # #TODO: jperla: security issue; needs to be escaped
    query_string = '&'.join('%s=%s' % (urllib.quote(k),urllib.quote(v)) for k,v in attrs.iteritems())
    u = '%s%s?%s' % (url, path, query_string)
    a = simplejson.loads(urllib2.urlopen(u).read())
    return a

wordnet_ws = partial(web_service, 'http://127.0.0.1:8092/')

from weby.middleware import EvalException
wrapped_app = weby.wsgify(app, EvalException)

if __name__ == '__main__':
    print 'Loading server...'
    #weby.http.server.serve(wrapped_app, host='127.0.0.1', port=8092, reload=False)
    weby.http.server.tornado.start(app, host='127.0.0.1', port=8096)

