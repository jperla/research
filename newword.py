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
    synset_id = req.params.get('synset', '').strip('\r\n ').lower()
    if query != u'' or synset_id != u'':
        if query != u'':
            synsets = wordnet_ws('synsets', {'query':query})
        elif synset_id != u'':
            synsets = [synset_id]
        ##TODO: jperla: only works because monosemous
        results = [(s, 
                    ranked_synonyms(s),
                    wordnet_ws('linked_gloss', {'synset': s}), 
                    wordnet_ws('relations', {'synset': s}),
                    imagenet_ws('images', {'synset':s}),
                    ) for s in synsets]
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
imagenet_ws = partial(web_service, 'http://127.0.0.1:8096/')
    

def normalize_frequency(s):
    total = 0.00001 + sum(math.log(1.0 + c) for w,c in s)
    return [(w, (math.log(1.0 + c)/total)) for w,c in s]
    
def lookup_query(query):
    results = frequencies_ws('frequencies', {'query':query})
    results = list(reversed(sorted(results, key=lambda r:sum(count for _,count in r))))
    results = results[:4]
    return [normalize_frequency(s) for s in results]


@weby.templates.sanitize_html()
@weby.template()
def template_index(p, query, results):
    with p(html.html()):
        with p(html.head()):
            p(html.title('%s - WordNet' % query))
        with p(html.body()):
            #p(html.a(html.h1('WordNet'), {'href':'/', 'style':'text-decoration:none;color:black;'}))
            with p(html.form({'action':'', 'method':'GET'})):
                p(html.input_text('query', query))
                p(html.input_submit(value='Search WordNet'))
            if not results == None:
                if results == []:
                    p(html.p('No synsets found'))
                else:
                    for result, synonyms, definition, relations, images in results:
                        p(partial_result(query, result, synonyms, definition, relations, images))

def link_to_synset(synset, word=None, type=''):
    if word is None:
        word = synset.split('.')[0].replace('_', ' ')
    return html.a_href('%s?synset=%s' % (index.url(), synset), word, {'class':type})
                        
@weby.template()
def partial_definition(p, definition):
    try:
        for w,s in definition[:-1]:
            if s is None:
                p(html.h(w))
            else:
                p(link_to_synset(s, w, 'gloss'))
            p(u' ')
    except:
        p(definition)
    
@weby.template()
def helper_linked_preview_image(p, image_url):
    p(html.a(html.img('', {'src':image_url, 'style':'max-width:150px;max-height:150px;'}), {'href':image_url, 'style':'border:0'}))

@weby.template()
def template_image_table(p, images):
    with p(html.table()):
        with p(html.tr()):
            with p(html.td()):
                if len(images) > 0:
                    p(helper_linked_preview_image(images[0]))
            with p(html.td()):
                if len(images) > 1:
                    p(helper_linked_preview_image(images[1]))
        with p(html.tr()):
            with p(html.td()):
                if len(images) > 2:
                    p(helper_linked_preview_image(images[2]))
            with p(html.td()):
                if len(images) > 3:
                    p(helper_linked_preview_image(images[3]))

def helper_synonym(query, lemma, count, max_count):
    lemma = lemma.replace('_', ' ')
    if query == lemma:
        lemma = html.b(lemma)
    if count > 0:
        c = html.span('%s %s' % (lemma, helper_count_box(count, max_count)))
    else:
        c = html.span('%s' % lemma)
    return c

@weby.templates.joined()
def helper_count_box(p, count, max_count):
    if count > 0:
        if max_count > 1:
            num_boxes = round((math.log(count) / math.log(max_count)) * 4)
        else:
            num_boxes = 4
    else:
        num_boxes = 0
    if num_boxes > 0:
        style = 'height:6px;width:6px;border:1px solid white;background-color:blue;position:absolute;'
        with p(html.div({'style':'display:inline;position:absolute;'})):
            if num_boxes >= 4:
                p(html.div(' ', {'style':'top:1px;left:6px;' + style}))
            if num_boxes >= 3:
                p(html.div(' ', {'style':'top:1px;left:-1px;' + style}))
            if num_boxes >= 2:
                p(html.div(' ', {'style':'top:8px;left:6px;' + style}))
            if num_boxes >= 1:
                p(html.div(' ', {'style':'top:8px;left:-1px;' + style}))
        p(html.nobreaks('   '))

def old_helper_synonym(query, lemma, count):
    lemma = lemma.replace('_', ' ')
    if query == lemma:
        lemma = html.b(lemma)
    if count > 0:
        c = html.span('%s (%s)' % (lemma, count))
    else:
        c = html.span('%s' % lemma)
    return c

@weby.template()
def partial_result(p, query, result, synonyms, definition, relations, images):
    with p(html.table({'style':'margin:20px;width:100%;'})):
        with p(html.tr()):
            with p(html.td({'valign':'top', 'width':'50%'})):
                p(partial_result_data(query, result, synonyms, definition, relations))
                p(html.nobreaks(' '))
            with p(html.td({'valign':'top', 'width':'50%'})):
                p(template_image_table(images))
                p(html.nobreaks(' '))

@weby.template()
def partial_result_data(p, query, result, synonyms, definition, relations):
    with p(html.table()):
        with p(html.tr()):
            with p(html.td()):
                max_count = max(c for _,c in synonyms)
                s = [helper_synonym(query, l, c, max_count) for l,c in synonyms]
                p(', '.join(s))
        with p(html.tr()):
            with p(html.td()):
                p(partial_definition(definition))
        with p(html.tr()):
            with p(html.td()):
                p(partial_relations(relations))

@weby.template()
def partial_relations(p, relations):
    larger = []
    smaller = []
    for relation,words in relations.iteritems():
        if 'part' in relation:
            type = 'part'
        elif 'substance' in relation:
            type = 'substance'
        elif 'member' in relation:
            type = 'member'
        else:
            type = 'kind'
        if 'hyper' in relation or 'holo' in relation:
            type += '-larger'
            larger.extend([(w, type) for w in words])
        else:
            type += '-smaller'
            smaller.extend([(w, type) for w in words])
    if len(larger) > 0 or len(smaller) > 0:
        with p(html.table()):
            with p(html.tr()):
                with p(html.td({'width':'50%', 'valign':'top'})):
                    q=[link_to_synset(s, type=t) for s,t in smaller]
                    p(u', '.join(q))
                with p(html.td({'width':'50%', 'valign':'top'})):
                    q=[link_to_synset(s, type=t) for s,t in larger]
                    p(u', '.join(q))

import pprint
import sys
import traceback


from weby.middleware import EvalException
wrapped_app = weby.wsgify(app, EvalException)

if __name__ == '__main__':
    print 'Loading server...'
    #weby.http.server.serve(wrapped_app, host='127.0.0.1', port=8089, reload=True)
    tornado_app = weby.http.server.tornado.start(app, port=8089)

