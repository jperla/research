#!/usr/bin/python
import math
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
    if query != "":
        results = lookup_query(query)
        ##TODO: jperla: only works because monosemous
        results = [(r, 
                    wordnet_ws('definition', r[0][0]), 
                    wordnet_ws('relations', r[0][0]))
                        for r in results]
    else:
        results = None
    page(template_index(query, results))

 
def web_service(url, argname, page, arg):
    # #TODO: jperla: security issue
    u = '%s%s?%s=%s' % (url, page, argname, arg)
    a = simplejson.loads(urllib2.urlopen(u).read())
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
        results.extend(frequencies_ws('frequencies', d))
    results.extend(frequencies_ws('frequencies', query))
    results = list(reversed(sorted(results, key=lambda r:sum(count for _,count in r))))
    results = results[:4]
    return [normalize_frequency(s) for s in results]

@weby.template()
def template_index(p, query, results):
    with p(html.html()):
        with p(html.head()):
            p(html.title('%s - WordNet' % query))
        with p(html.body()):
            p(html.h1('WordNet'))
            with p(html.form({'action':'', 'method':'GET'})):
                p(html.input_text('query', query))
                p(html.input_submit('Search'))
            if results is not None:
                if results == []:
                    p(html.p('No monosemous synsets found'))
                else:
                    for result, definition, relations in results:
                        p(partial_result(result, definition, relations))
                        
    
@weby.template()
def partial_result(p, result, definition, relations):
  with p(html.div({'style':'padding-right:20px;float:left;width:150px;'})):
    p(html.p(definition))
    with p(html.table()):
        for lemma,count in result:
            with p(html.tr()):
                p(html.td(lemma))
            with p(html.tr()):
                bar = {'style':'color:blue;height:1px;width:%spx;' % int(count*100)}
                if int(count*100) > 2:
                    p(html.td('<div style="border:1px solid blue;color:blue;height:0px;width:%spx;">&nbsp;</div>' % int(count*100)))
    for relation,words in relations.iteritems():
        if len(words) > 0:
            p(html.b(relation))
            with p(html.ul()):
                for w in words:
                    p(html.li(html.ahref(index.url() + '?query=' + w, w)))

from weby.middleware import EvalException
wrapped_app = weby.wsgify(app, EvalException)

if __name__ == '__main__':
    print 'Loading server...'
    weby.http.server.serve(wrapped_app, host='127.0.0.1', port=8089, reload=True)

