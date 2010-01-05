#!/usr/bin/python
import urllib2

import nltk
from nltk.corpus import wordnet as wn
import simplejson

import weby
from weby.templates.helpers import html

app = weby.defaults.App()

def synset_from_params(params):
    '''Tries to get synset from synset id,
       or otherwise tries to get synset from
       the query'''
    synset_id = params.get('synset', None)
    if synset_id is not None:
        try:
            synset = wn.synset(synset_id)
        except: 
            pass
        else:
            return synset
    query = params.get('query', u'').strip('\r\n ').lower()
    synsets = wn.synsets(query.replace(' ', '_'))
    if synsets == []:
        return None
    else:
        return synsets[0]

def synset_service(attribute, call_attribute=True, extract_lemmas=True):
    @weby.urlable_page()
    def synset_attribute_service(req, page):
        synset = synset_from_params(req.params)
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
    
@app.subapp('synsets')
@weby.urlable_page()
def synsets_service(req, page):
    query = req.params.get('query', None)
    if query is not None:
        synsets = wn.synsets(query.replace(' ', '_'))
        page(unicode(simplejson.dumps([s.name for s in synsets])))
    else:
        page(unicode(simplejson.dumps(None)))

@app.subapp('synset_pos_offset')
@weby.urlable_page()
def synset_pos_offst(req, page):
    synset = synset_from_params(req.params)
    if synset is not None:
        page(unicode(simplejson.dumps(offset_str(synset))))
    else:
        page(unicode(simplejson.dumps(None)))


synonyms_view = synset_service('lemma_names', False, False)
synonyms_view = app.subapp('synonyms')(synonyms_view)

definition_view = synset_service('definition', False, False)
definition_view = app.subapp('definition')(definition_view)

'''
#images
http://www.image-net.org/api/text/imagenet.synset.geturls?wnid=n02084071
'''
def link_word(w):
    stopwords = set([
                    'a', 'the', 'can', 'be', 'is', 'or', 'as',
                    'in', 'an', 'has', 'by', 'it', 'its',
                    ])
    if w in stopwords:
        return None
    synsets = wn.synsets(w)
    if len(synsets) == 0:
        return None
    else:
        return synsets[0].lemma_names[0]

def link_definition(synset):
    linked = [(w, link_word(w)) for w in synset.definition.split(' ')]
    return linked

@app.subapp('linked_definition')
@weby.urlable_page()
def linked_definition(req, page):
    synset = synset_from_params(req.params)
    if synset is not None:
        linked = link_definition(synset)
        page(unicode(simplejson.dumps(linked)))
    else:
        page(unicode(simplejson.dumps(None)))

@app.subapp('linked_gloss')
@weby.urlable_page()
def linked_gloss(req, page):
    synset = synset_from_params(req.params)
    def link_gloss(synset):
        linked = linked_gloss(synset)
        if linked is None:
            return synset.definition
        else:
            sentence = []
            for w,s in linked:
                if s is None:
                    sentence.append((w, None))
                else:
                    sentence.append((w, s.name))
            return sentence
    if synset is not None:
        linked = link_gloss(synset)
        page(unicode(simplejson.dumps(linked)))
    else:
        page(unicode(simplejson.dumps(None)))

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
    synset = synset_from_params(req.params)
    relations = {}
    if synset is not None:
        for r in relation_attributes:
            relations[r] = [s.name for s in getattr(synset, r)()]
    page(unicode(simplejson.dumps(relations)))

hypernyms = app.subapp('hypernyms')(synset_service('hypernyms'))
hyponyms = app.subapp('hyponyms')(synset_service('hyponyms'))
app.subapp('part_meronyms')(synset_service('part_meronyms'))
app.subapp('part_holonyms')(synset_service('part_holonyms'))
app.subapp('member_meronyms')(synset_service('member_meronyms'))
app.subapp('member_holonyms')(synset_service('member_holonyms'))
app.subapp('substance_meronyms')(synset_service('substance_meronyms'))
app.subapp('substance_holonyms')(synset_service('substance_holonyms'))


index_from_sense = simplejson.loads(open('index_from_sense.json', 'r').read())
lemma_from_index = simplejson.loads(open('lemma_from_index.json', 'r').read())
gloss_adv = simplejson.loads(open('gloss_adv.json', 'r').read())
gloss_adj = simplejson.loads(open('gloss_adj.json', 'r').read())
gloss_verb = simplejson.loads(open('gloss_verb.json', 'r').read())
gloss_noun = simplejson.loads(open('gloss_noun.json', 'r').read())

def synset_from_sense(sense):
    i = index_from_sense.get(sense, None)
    lemma = lemma_from_index.get(i, None)
    if lemma is None:
        return None
    else:
        synset = None
        synsets = wn.synsets(lemma)
        for s in synsets:
            if s.offset == int(i):
                synset = s
        return synset

def offset_str(synset):
    offset_str = str(synset.offset)
    offset_str = ((8 - len(offset_str)) * '0') + offset_str
    return synset.pos + offset_str

def linked_gloss(synset):
    if synset.pos == wn.NOUN:
        gloss = gloss_noun.get(offset_str(synset), None)
    elif synset.pos == wn.VERB:
        gloss = gloss_verb.get(offset_str(synset), None)
    elif synset.pos == wn.ADJ:
        gloss = gloss_adj.get(offset_str(synset), None)
    elif synset.pos == wn.ADV:
        gloss = gloss_adv.get(offset_str(synset), None)
    else:
        return None
    if gloss is None:
        return None
    else:
        gloss = [(lemma, synset_from_sense(sense)) for lemma,sense in gloss]
        return gloss





from weby.middleware import EvalException
wrapped_app = weby.wsgify(app, EvalException)

if __name__ == '__main__':
    synsets = wn.synsets('word')
    print 'Loading server...'
    #weby.http.server.serve(wrapped_app, host='127.0.0.1', port=8092, reload=False)
    weby.http.server.tornado.start(app, host='127.0.0.1', port=8092)

