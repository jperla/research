import nltk
from nltk.corpus import wordnet as wn

polysemy = {}
#takes about 1 minute
for s in wn.all_synsets():
    for w in s.lemma_names:
        polysemy[w] = polysemy.get(w, []) + [s]
        
monosemous_words = dict((w,s[0]) for w,s in polysemy.iteritems() if len(s) == 1)

partially_monosemous_synsets = set(s for w,s in monosemous_words.iteritems())

only_monosemous_synsets = [s for s in wn.all_synsets() 
                        if all(w in monosemous_words for w in s.lemma_names)]

lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()

from nltk.corpus import brown

lemma_frequency = {}
lemmas = {}
for synset in only_monosemous_synsets:
    lemmas[synset] = synset.lemma_names
    for lemma in lemmas[synset]:
        lemma_frequency[lemma] = 0

#takes ~5 minutes
for w in brown.words():
    lemma = lemmatizer.lemmatize(w)
    if lemma in lemma_frequency:
        lemma_frequency[lemma] += 1

frequency = {}
for synset in lemmas:
    frequency[synset] = sum(lemma_frequency[lemma] 
                                    for lemma in lemmas[synset])

total = 1161192
ranked = list(reversed(sorted([(synset, frequency[synset], total) 
                                for synset in only_monosemous_synsets],
                         key=lambda t: t[1])))

def sort_lemmas(lemmas):
    lemmas = list(lemmas)
    a = list(reversed(sorted([(lemma, lemma_frequency[lemma])
                            for lemma in lemmas], key=lambda x:x[1])))
    return a

ranked_lemmas = [(sort_lemmas(s.lemma_names), b, c) for s,b,c in ranked]



