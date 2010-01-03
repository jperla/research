import simplejson
from pyquery import PyQuery as pq

def tagged_sentence_from_xml(wfs):
    sentence = []
    for i in xrange(len(wfs)):
        wf = wfs.eq(i)
        word = wf.text()
        tag = wf('id').attr('sk')
        sentence.append((word, tag))
    return sentence

def get_glosses():
    filename = 'WordNet-3.0/glosstag/merged/' + 'noun.xml'
    text = open(filename, 'r').read()
    doc = pq(text)

    sentences = {}
    synsets = doc('synset')
    for i in xrange(len(synsets)):
        s = synsets.eq(i)
        id = s.attr('id')
        wfs = s('def')('wf,cf')
        sentence = tagged_sentence_from_xml(wfs)
        sentences[id] = sentence

    print simplejson.dumps(sentences)

def get_indices_from_senses():
    data = open('/home/jperla/nltk_data/corpora/wordnet/index.sense', 'r').read()
    lines = data.split('\n')[:-1]
    split_lines = [line.split(' ') for line in lines]
    mapping = dict([(s[0], s[1]) for s in split_lines])
    print simplejson.dumps(mapping)

def get_lemma_from_index():
    mapping = {}
    mapping.update(get_lemma_from_index_from_filename('/home/jperla/nltk_data/corpora/wordnet/data.noun'))
    mapping.update(get_lemma_from_index_from_filename('/home/jperla/nltk_data/corpora/wordnet/data.adj'))
    mapping.update(get_lemma_from_index_from_filename('/home/jperla/nltk_data/corpora/wordnet/data.adv'))
    mapping.update(get_lemma_from_index_from_filename('/home/jperla/nltk_data/corpora/wordnet/data.verb'))
    print simplejson.dumps(mapping)

def get_lemma_from_index_from_filename(filename):
    data = open(filename, 'r').read()
    lines = data.split('\n')[:-1]
    split_lines = [line.split(' ') for line in lines]
    mapping = dict([(s[0], s[4]) for s in split_lines])
    return mapping

def linked_gloss(synset):
    offset_str = str(synset.offset)
    offset_str = ((8 - len(offset_str)) * '0') + offset_str
    if synset.pos == wn.ADV:
        gloss = gloss_adv.get('r' + offset_str, None)
    else:
        raise
    if gloss is None:
        return None
    else:
        gloss = [(lemma, synset_from_sense(sense)) for lemma,sense in gloss]
        return gloss

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

