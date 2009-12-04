#!/usr/bin/python
import urllib2

import nltk
from nltk.corpus import wordnet as wn
import simplejson

import weby
from weby.templates.helpers import html

app = weby.defaults.App()

def synset_from_word(w):
    w = w.strip('\r\n ').lower()
    synsets = wn.synsets(w)
    if synsets == []:
        return None
    else:
        return synsets[0]

def synset_service(attribute, call_attribute=True, extract_lemmas=True):
    @weby.urlable_page()
    def synset_attribute_service(req, page):
        synset = synset_from_word(req.params.get('word', u''))
        if synset is not None:
            a = getattr(synset, attribute)
            if call_attribute:
                a = a()
            if extract_lemmas:
                a = [s.lemma_names[0] for s in a]
            page(unicode(simplejson.dumps(a)))
        else:
            page(unicode(simplejson.dumps(None)))
        
    return synset_attribute_service
    

definition_view = synset_service('definition', False, False)
definition_view = app.subapp('definition')(definition_view)

examples_view = synset_service('examples', False, False)
examples = app.subapp('examples')(examples_view)

@app.subapp('relations')
@weby.urlable_page()
def relations(req, page):
    relation_attributes = [
        'hypernyms', 'hyponyms',
        'part_meronyms', 'part_holonyms',
        'substance_meronyms', 'substance_holonyms',
        'member_meronyms', 'member_holonyms',
    ]
    synset = synset_from_word(req.params.get('word', ''))
    relations = {}
    if synset is not None:
        for r in relation_attributes:
            relations[r] = [s.lemma_names[0] for s in getattr(synset, r)()]
    page(unicode(simplejson.dumps(relations)))

hypernyms = app.subapp('hypernyms')(synset_service('hypernyms'))
hyponyms = app.subapp('hyponyms')(synset_service('hyponyms'))
app.subapp('part_meronyms')(synset_service('part_meronyms'))
app.subapp('part_holonyms')(synset_service('part_holonyms'))
app.subapp('member_meronyms')(synset_service('member_meronyms'))
app.subapp('member_holonyms')(synset_service('member_holonyms'))
app.subapp('substance_meronyms')(synset_service('substance_meronyms'))
app.subapp('substance_holonyms')(synset_service('substance_holonyms'))


from weby.middleware import EvalException
wrapped_app = weby.wsgify(app, EvalException)

if __name__ == '__main__':
    synsets = wn.synsets('word')
    print 'Loading server...'
    weby.http.server.serve(wrapped_app, host='127.0.0.1', port=8092, reload=True)

