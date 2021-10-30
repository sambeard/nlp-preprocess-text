from functools import reduce
from os import write
from pickle import FALSE
import pronouncing
from nltk.tokenize import word_tokenize
import re
import string
import prosodic
prosodic.config['print_to_screen'] = 0
prosodic.config['en_TTS_ENGINE'] = 1

METER_LIMIT = 5
METER_LINE_LIMIT = 120 # The longer the line the longer it takes to analyze, so let's just skip them for speed

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
        syllables = set([pronouncing.syllable_count(ph) for ph in phs])
        syllables = syllables if len(syllables) > 0 else estimate_syllables(tokens[i])
        syllables = list(set(syllables))
        all_syllables.append(syllables)

    possible_total_syllables = reduce(lambda x,y: [ i+n for i in x for n in y], all_syllables,[0])
    
    return 17 in set(possible_total_syllables)

def get_stresses(line):
    text = prosodic.Text(line)
    text.parse(meter='default_english')
    parses = text.bestParses()
    stresses = []
    for parse in parses:
        if parse is None:
            continue
        meter = ""
        for pos in parse.positions:
            val = pos.meterVal
            if val == "w":
                meter += "0" # I just prefer this representation
            elif val == "s":
                meter += "1"
        stresses.append(meter)
    return stresses

def stresses_to_meter(stresses):
    meter_table = {
        "01": "Iambic",
        "10": "Trochaic",
        "11": "Spondaic",
        "001": "Anapestic",
        "100": "Dactylic",
        "010": "Amphibrachic",
        "00": "Pyrrhic"
    }
    '''
    This is an ambiguous state machine, let's use the following flags:
    0: No meter found.
    n: End of state, found n copies.
    -n: End of state, go back n, also move pointer back n
    In all cases, simply grab the correct one from the table
    '''
    meter_tree = {
        "0": {
            "0": {
                "0": { # 00, third 0 is second set of 00. This could be done with -1 but let us continue for speed
                    "0": 2,
                    "1": 0 # Found 00 01 which is not a valid consistent meter
                }, 
                "1": 1 # Must be 001
            },
            "1": {
                "0": { # Ambiguous, need next token
                    "0": -1, # You could expand this state but that's ugly (010 010)
                    "1": 2
                },
                "1": 0
            }
        },
        "1": {
            "0": {
                "0": 1,
                "1": {
                    "0": 2,
                    "1": 0
                }
            },
            "1": {
                "0": 0,
                "1": {
                    "0": 0,
                    "1": 2
                }
            }
        }
    }
    count_table = {
        1: "monometer",
        2: "dimeter",
        3: "trimeter",
        4: "tetrameter",
        5: "pentameter",
        6: "hexameter",
        7: "heptameter",
        8: "octameter"
    }
    pointer = 0
    stack = ""
    counter = 0
    sub_tree = meter_tree
    while pointer < len(stresses) and counter == 0:
        val = stresses[pointer]
        if val == "2":
            val = "1"
        stack += val
        sub_tree = sub_tree[val]
        if not isinstance(sub_tree, dict): # We have found a leaf
            if sub_tree == 0:
                return None
            elif sub_tree < 0:
                pointer += sub_tree
                add = abs(sub_tree)
            else:
                add = sub_tree
                pointer += 1
            counter += add
            stack = stack[:(add//2)+1]
        else:
            pointer += 1
    if counter == 0 or len(stresses) % len(stack) != 0:
        return None
    else: # We have found a pattern, now to see if it repeats
        patt_pointer = 0
        while pointer < len(stresses):
            val = stresses[pointer]
            req = stack[patt_pointer]
            if val != req:
                return None
            pointer += 1
            patt_pointer += 1
            if patt_pointer >= len(stack):
                counter += 1
                patt_pointer = 0
    style = meter_table[stack]
    foot = counter
    if foot in count_table:
        foot = count_table[foot]
    return style + " " + str(foot)

def get_meter(poem):
    meters = []
    lines = poem.splitlines()
    if len(lines) < 2:
        return None
    for line in lines[:METER_LIMIT]:
        if len(line) <= METER_LINE_LIMIT:
            stresses = get_stresses(line)
            line_meters = []
            for stress in stresses:
                meter = stresses_to_meter(stress)
                line_meters.append(meter)
            meters.append(line_meters)
    scores = {}
    for meter in meters:
        for line_meter in meter:
            if line_meter in scores:
                scores[line_meter] += 1
            else:
                scores[line_meter] = 1
    scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
    return scores

def get_styles(poem, window_size=4):
    poem = re.sub(r"(\w+)-(\w+)",r"\1 \2",poem)
    tokens = [token for token in word_tokenize(poem) if not re.match(r"[^\w]+", token)]
    phonemes_for_tokens = [pronouncing.phones_for_word(t) for t in tokens]

    (alliterations, assonances) = alliteration_and_assonance(tokens, phonemes_for_tokens, window_size)

    meter = get_meter(poem)
    main_meter = None
    if meter:
        main_meter = meter[0][0]
        if main_meter is None and len(meter) > 1: # If it can't analyze most of the lines properly
            main_meter = meter[1][0]

    return {
        "form":{
            "is_haiku": is_haiku(tokens, phonemes_for_tokens),
        },
        "rhyme": {
            "alliteration": len(alliterations)/max(1,len(tokens)),
            "assonance": len(assonances)/max(1,len(tokens))
        },
        "meter": {
            "main": main_meter,
            "all": meter
        }
    }