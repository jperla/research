#!/usr/bin/python
import math
import urllib2
from functools import partial

import simplejson

import webify
from webify.templates.helpers import html

app = webify.defaults.app()

@app.subapp(path='/')
@webify.urlable()
def index(req, p):
    query = req.params.get('query', '').strip('\r\n ').lower()
    if query != "":
        results = lookup_query(query)
        ##TODO: jperla: only works because monosemous
        results = [(r, 
                    wordnet_ws('definition', r[0][0]), 
                    wordnet_ws('relations', r[0][0]))
                        for r in results]
    else:
        results = None
    p(template_index(query, results))

 
def web_service(url, argname, page, arg):
    # #TODO: jperla: security issue
    u = '%s%s?%s=%s' % (url, page, argname, arg)
    print u
    a= simplejson.loads(urllib2.urlopen(u).read())
    return a

frequencies_ws = partial(web_service, 'http://127.0.0.1:8090/', 'query')
wordnet_ws = partial(web_service, 'http://127.0.0.1:8092/', 'word')
    

def normalize_frequency(s):
    total = 0.00001 + sum(math.log(1.0 + c) for w,c in s)
    return [(w, (math.log(1.0 + c)/total)) for w,c in s]
    
def lookup_query(query):
    #results = inverted_ranked_lemmas.get(query, [])
    defragmented = frequencies_ws('defragment', query)
    results = []
    for d in defragmented:
        results.extend(frequencies_ws('', d))
    results.extend(frequencies_ws('', query))
    results = list(reversed(sorted(results, key=lambda r:sum(count for _,count in r))))
    results = results[:4]
    return [normalize_frequency(s) for s in results]

@webify.template()
def template_index(t, query, results):
    with t(html.html()):
        with t(html.head()):
            t(html.title('%s - WordNet' % query))
        with t(html.body()):
            t(html.h1('WordNet'))
            with t(html.form(action='', method='GET')):
                t(html.input_text('query', query))
                t(html.input_submit('Search'))
            if results is not None:
                if results == []:
                    t(html.p('No monosemous synsets found'))
                else:
                    for result, definition, relations in results:
                        t(partial_result(result, definition, relations))
                        
    
@webify.template()
def partial_result(t, result, definition, relations):
  with t(html.div({'style':'padding-right:20px;float:left;width:150px;'})):
    t(html.p(definition))
    with t(html.table()):
        for lemma,count in result:
            with t(html.tr()):
                t(html.td(lemma))
            with t(html.tr()):
                bar = {'style':'color:blue;height:1px;width:%spx;' % int(count*100)}
                if int(count*100) > 2:
                    t(html.td('<div style="border:1px solid blue;color:blue;height:0px;width:%spx;">&nbsp;</div>' % int(count*100)))
    for relation,words in relations.iteritems():
        if len(words) > 0:
            t(html.b(relation))
            with t(html.ul()):
                for w in words:
                    t(html.li(html.a(index.url() + '?query=' + w, w)))

from webify.middleware import EvalException
wrapped_app = webify.wsgify(app, EvalException)

if __name__ == '__main__':
    print 'Loading server...'
    webify.http.server.serve(wrapped_app, host='127.0.0.1', port=8089, reload=True)

