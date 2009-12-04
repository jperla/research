#!/usr/bin/python
import urllib2

import nltk
from nltk.corpus import wordnet as wn
import simplejson

import webify
from webify.templates.helpers import html

app = webify.defaults.app()

def synset_from_word(w):
    w = w.strip('\r\n ').lower()
    synsets = wn.synsets(w)
    if synsets == []:
        return None
    else:
        return synsets[0]

def synset_service(attribute, call_attribute=True, extract_lemmas=True):
    @webify.urlable()
    def synset_attribute_service(req, p):
        synset = synset_from_word(req.params.get('word', ''))
        if synset is not None:
            a = getattr(synset, attribute)
            if call_attribute:
                a = a()
            if extract_lemmas:
                a = [s.lemma_names[0] for s in a]
            p(unicode(simplejson.dumps(a)))
        else:
            p(u'null')
        
    return synset_attribute_service
    

definition_view = synset_service('definition', False, False)
app.subapp('/definition')(definition_view)

examples_view = synset_service('examples', False, False)
app.subapp('/examples')(definition_view)

@app.subapp('/relations')
@webify.urlable()
def relations(req, p):
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
    p(unicode(simplejson.dumps(relations)))

app.subapp('/hypernyms')(synset_service('hypernyms'))
app.subapp('/hyponyms')(synset_service('hyponyms'))
app.subapp('/part_meronyms')(synset_service('part_meronyms'))
app.subapp('/part_holonyms')(synset_service('part_holonyms'))
app.subapp('/member_meronyms')(synset_service('member_meronyms'))
app.subapp('/member_holonyms')(synset_service('member_holonyms'))
app.subapp('/substance_meronyms')(synset_service('substance_meronyms'))
app.subapp('/substance_holonyms')(synset_service('substance_holonyms'))


from webify.middleware import EvalException
wrapped_app = webify.wsgify(app, EvalException)

if __name__ == '__main__':
    print 'Loading server...'
    webify.http.server.serve(wrapped_app, host='127.0.0.1', port=8092, reload=True)

