from functools import reduce
from os import write
from pickle import FALSE
import pronouncing
from nltk.tokenize import word_tokenize
import re


PHONEME_TO_TYPE = dict({(k,v[0]) for (k,v) in pronouncing.cmudict.phones()})

TYPE_TO_PHONEMES = {}
for k in set([i for i in PHONEME_TO_TYPE.values()]):
    TYPE_TO_PHONEMES[k] = [v for v in PHONEME_TO_TYPE if PHONEME_TO_TYPE[v]==k]

def alliterates(phoneme1, phoneme2):
    if(not(phoneme1 and phoneme2)):
        return False
    return phoneme1.split()[0] == phoneme2.split()[0]

def alliteration_and_assonance(tokens, phoneme_list, window_size):
    alliterations = []
    assonances = []
    window_size = min(len(tokens),window_size)-1
    for i in range(1,len(tokens)):
        for j in range(-min(window_size,i), 0):
            (po,pb) = (phoneme_list[i+j], phoneme_list[i])
            t = (tokens[i+j], tokens[i])
            if(any([alliterates(o,b) for o in po for b in pb])):
                alliterations.append(t)
            for o in po:
                for b in pb:
                    (vo, vb) = tuple(map(lambda ps: [p for p in ps.split() if p[:-1] in TYPE_TO_PHONEMES['vowel'] and int(p[-1]) >0],(o,b)))
                    if len(set(vo).intersection(set(vb))):
                        assonances.append(t)
                        
    return (alliterations,assonances)


def estimate_syllables(word):
    approx = int(.6 + len(word)/3.2)
    _range = max(3, int(len(word)/3))
    return [ max(1, (i - int(_range/2)  + approx)) for i in range(_range)]

def is_haiku(tokens, phoneme_list):
    if(len(tokens)>17):
        return False

    all_syllables = []
    
    for (i,phs) in enumerate(phoneme_list):
        syllables = set(phs)
        syllables = syllables if len(syllables) > 0 else estimate_syllables(tokens[i])
        syllables = list(set(syllables))
        all_syllables.append(syllables)

    possible_total_syllables = reduce(lambda x,y: [ i+n for i in x for n in y], all_syllables,[0])
    
    return 17 in set(possible_total_syllables)    

def get_styles(poem, window_size=4):
    poem = re.sub(r"(\w+)-(\w+)",r"\1 \2",poem)
    tokens = [token for token in word_tokenize(poem) if not re.match(r"[^\w]+", token)]
    phonemes_for_tokens = [pronouncing.phones_for_word(t) for t in tokens]

    (alliterations, assonances) = alliteration_and_assonance(tokens, phonemes_for_tokens, window_size)

    return {
        "form":{
            "is_haiku": is_haiku(tokens, phonemes_for_tokens),
        },
        "rhyme": {
            "alliteration": len(alliterations)/len(tokens),
            "assonance": len(assonances)/len(tokens)
        }
    }