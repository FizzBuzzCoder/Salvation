import ast
import json
import os
import re

import numpy as np
import pandas as pd
from nltk.stem import WordNetLemmatizer
from numpy.random import normal, uniform
from scipy import stats

# STOP is a list of Stopwords (words that are explicitly not used during analysis)
STOP = [i.replace("\n", "") for i in open("stopwords.txt")]
STOP += '''
zero one two three four five six seven eight nine ten eleven twelve
thirteen fourteen fifteen sixteen seventeen eighteen nineteen
twenty thirty forty fifty sixty seventy eighty ninety hundred
thousand million billion trillion quadrillion quintillion sextillion septillion
first second third fourth fifth sixth seventh eigth ninth tenth
hesitation okay ok alright yeah good thank yes all right correct
phone number email address calling call thank homeowner
week month year morning evening day days night nights hour hours weekend evening time
yesterday today tomorrow date
sunday monday tuesday wednesday thursday friday saturday
january february march april may june july august september october november december
'''.split()
STOP = set(STOP)

def clean(text, stopwords=None):
    '''
    Cleans a text to make it ready for analysis
    Input (str): Text to be cleaned
    Output (str): Cleaned text
    '''
    
    text = text.lower()
    text = re.sub(r"[^a-z0-9!@#\$%\^\&\*_\-,\.' ]", ' ', text)
    text = re.sub(r"[^a-z' ]", ' ', text)
    text = text.split()
    lemm = WordNetLemmatizer()
    text = [lemm.lemmatize(w) for w in text]
    if stopwords:
        text = [w for w in text if w not in stopwords]
    text = [w for w in text if len(w) > 3]
    
    return " ".join(text)


original_set = set(['asphalt', 'attic', 'avocado', 'baseboard', 'bath', 'bathroom', 'bed',
 'bedroom', 'blown', 'brick', 'broken', 'cabinet', 'camera', 'carpet', 'cat',
 'cautious', 'ceiling', 'coming', 'content', 'contents', 'damage', 'damaged',
 'delray', 'description', 'discard', 'dog', 'door', 'electricity',
 'electronics', 'exterior', 'fell', 'fence', 'fences', 'flat', 'flooding',
 'floor', 'florida', 'food', 'front', 'furniture', 'garage', 'give', 'glass',
 'gutter', 'hang', 'happen', 'hit', 'hole', 'home', 'inside', 'interior',
 'kind', 'kitchen', 'largo', 'leak', 'leakage', 'leaking', 'lexus', 'livable',
 'live', 'long', 'lose', 'lost', 'nano', "neighbor's", 'nellie', 'picture',
 'irma', 'lost',
 'pictures', 'power', 'pullout', 'rear', 'receipt', 'reorder', 'repair',
 'repeat', 'roof', 'rooftop', 'room', 'rooms', 'salvageable', 'sample', 'shed',
 'shingle', 'shingles', 'show', 'side', 'single', 'singles', 'spoilage', 'tent',
 'thick', 'tile', 'tiles', 'tree', 'trees', 'uprooted', 'wall', 'wanted',
 'washroom', 'water', 'window', 'wood', 'yard'])


exterior_set = """
exterior asphalt damage damaged roof roofs brick break broken damaged
door fell fall fallen fence fences flat flooding front garage glass gutter damages 
hit hole holes lost neighbor neighbor's neighbors rear rooftop shed blown damage hit hits
shingle single shingles singles thick tile tiles tree trees uprooted wall window water wood
yard
"""
exterior_set = set(exterior_set.split())


interior_set = """
interior attic attics baseboard bath bathroom bed beds bedroom  cabinet carpet cat dog
ceiling content contents damage damages damaged flooding floor floors flooring food lost
furniture inside kitchen living room rooms spoil spoilage spoiled washroom window
damages bathroom
"""
interior_set = set(interior_set.split())


damage_set = """
damage damages lost claim property hurricane 
"""
damage_set = set(damage_set.split())

total_words = original_set.union(exterior_set, interior_set, damage_set)

def get_fuzzy_intent(text):
    text = clean(text).split()
    p, q, r = 0, 0, 0
    _p, _q, _r = [], [], []
    for w in text:
        if w in exterior_set: 
            p += 1
            _p.append(w)
        if w in interior_set: 
            q += 1
            _q.append(w)
        if w in damage_set: 
            r += 1
            _r.append(w)
                
    if r > 0 and r >= p and r >= q: return {"damage": set(_r)}
    if p > 0 and p >= q and p >= r: return {"exterior": set(_p)}
    if q > 0 and q >= p and q >= r: return {"interior": set(_q)}
    return dict()
