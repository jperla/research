#!/usr/bin/python
import simplejson
import weby
from weby.templates.helpers import html

app = weby.defaults.App()

@app.subapp('frequencies')
@weby.urlable_page()
def defragment(req, page):
    query = req.params.get('query', '').strip('\r\n ').lower()
    results = inverted_ranked_lemmas.get(query, [])
    page(unicode(simplejson.dumps(results)))

@app.subapp('defragment')
@weby.urlable_page()
def defragment(req, page):
    query = req.params.get('query', '').strip('\r\n ').lower()
    fragments = indexed_fragments.get(query, [])
    json = unicode(simplejson.dumps(fragments))
    page(json)


def read_ranked_lemmas(filename='ranked_lemmas_compressed.json'):
     return simplejson.loads(open(filename, 'r').read())

def invert_ranked_lemmas(ranked_lemmas):
    inverted = {}
    for r in ranked_lemmas:
        synset = r[0]
        for lemma, count in synset:
            inverted[lemma] = inverted.get(lemma, []) + [synset]
    return inverted

def index_fragments(r):
    fragments = {}
    for lemma in r:
        for i in xrange(3, len(lemma)):
            f = lemma[0:i].lower()
            fragments[f] = fragments.get(f, []) + [lemma]
    return fragments

ranked_lemmas = read_ranked_lemmas()
inverted_ranked_lemmas = invert_ranked_lemmas(ranked_lemmas)
indexed_fragments = index_fragments(inverted_ranked_lemmas)

from weby.middleware import EvalException
wrapped_app = weby.wsgify(app, EvalException)

if __name__ == '__main__':
    print 'Loading server...'
    weby.http.server.serve(wrapped_app, host='127.0.0.1', port=8090, reload=True)

