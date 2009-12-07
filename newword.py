#!/usr/bin/python
import math
import urllib
import urllib2
from functools import partial

import simplejson

import weby
from weby.templates.helpers import html

app = weby.defaults.App()

@app.subapp('')
@weby.urlable_page()
def index(req, page):
    query = req.params.get('query', '').strip('\r\n ').lower()
    if query != u'':
        synsets = wordnet_ws('synsets', {'query':query})
        ##TODO: jperla: only works because monosemous
        results = [(s, 
                    ranked_synonyms(s),
                    wordnet_ws('linked_definition', {'synset': s}), 
                    wordnet_ws('relations', {'synset': s}))
                        for s in synsets]
    else:
        results = None
    page(template_index(query, results))

def ranked_synonyms(synset):
    synonyms = wordnet_ws('synonyms', {'synset':synset})
    if len(synonyms) > 0:
        frequencies = frequencies_ws('frequencies', {'query':synonyms[0]})
        if len(frequencies) > 0:
            return [(f[0], f[1]) for row in frequencies for f in row ]
        else:
            return [(s,0) for s in synonyms]
    else:
        return []

 
def web_service(url, path, attrs):
    # #TODO: jperla: security issue; needs to be escaped
    query_string = '&'.join('%s=%s' % (urllib.quote(k),urllib.quote(v)) for k,v in attrs.iteritems())
    u = '%s%s?%s' % (url, path, query_string)
    a = simplejson.loads(urllib2.urlopen(u).read())
    return a

frequencies_ws = partial(web_service, 'http://127.0.0.1:8090/')
wordnet_ws = partial(web_service, 'http://127.0.0.1:8092/')
    

def normalize_frequency(s):
    total = 0.00001 + sum(math.log(1.0 + c) for w,c in s)
    return [(w, (math.log(1.0 + c)/total)) for w,c in s]
    
def lookup_query(query):
    results = frequencies_ws('frequencies', {'query':query})
    results = list(reversed(sorted(results, key=lambda r:sum(count for _,count in r))))
    results = results[:4]
    return [normalize_frequency(s) for s in results]

'''
# Did substring lookup but that sucks
def lookup_query(query):
    #results = inverted_ranked_lemmas.get(query, [])
    defragmented = frequencies_ws('defragment', {'query':query})
    results = []
    for d in defragmented:
        results.extend(frequencies_ws('frequencies', {'query':d}))
    results.extend(frequencies_ws('frequencies', {'query':query}))
    results = list(reversed(sorted(results, key=lambda r:sum(count for _,count in r))))
    results = results[:4]
    return [normalize_frequency(s) for s in results]
'''

@weby.templates.sanitize_html()
@weby.template()
def template_index(p, query, results):
    with p(html.html()):
        with p(html.head()):
            p(html.title('%s - WordNet' % query))
        with p(html.body()):
            p(html.h1('WordNet'))
            with p(html.form({'action':'', 'method':'GET'})):
                p(html.input_text('query', query))
                p(html.input_submit(value='Search'))
            if not results == None:
                if results == []:
                    p(html.p('No synsets found'))
                else:
                    for result, synonyms, definition, relations in results:
                        p(partial_result(result, synonyms, definition, relations))
                        
    
@weby.template()
def partial_result(p, result, synonyms, definition, relations):
  with p(html.div({'style':'padding-left:20px;width:650px;'})):
    p(html.b(u'%s: ' % result))
    for w,s in definition:
        if s is None:
            p(html.h(w))
        else:
            p(html.ahref(index.url() + '?query=' + s, w))
        p(u' ')
    with p(html.ul({'style':'padding-top:0px;padding-bottom:0px;'})):
      with p(html.li()):
          s = [html.span('%s (%s)' % (lemma,count)) for lemma,count in synonyms]
          p(', '.join(s))
          '''
          with p(html.tr()):
              bar = {'style':'color:blue;height:1px;width:%spx;' % int(count*100)}
              if int(count*100) > 2:
                  p(html.td('<div style="border:1px solid blue;color:blue;height:0px;width:%spx;">&nbsp;</div>' % int(count*100)))
          '''
      for relation,words in relations.iteritems():
        if len(words) > 0:
          with p(html.li()):
            p(html.b('%s: ' % relation))
            q=['%s' % html.ahref(index.url()+'?query='+w, w) for w in words]
            p(', '.join(q))

from weby.middleware import EvalException
wrapped_app = weby.wsgify(app, EvalException)

if __name__ == '__main__':
    print 'Loading server...'
    #weby.http.server.serve(wrapped_app, host='127.0.0.1', port=8089, reload=True)
    tornado_app = weby.http.server.tornado.start(app, port=8089)

