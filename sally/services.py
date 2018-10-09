import re
import string
import sys
from collections import defaultdict

from fuzzywuzzy import fuzz
from duckling import DucklingWrapper
dwrap = DucklingWrapper()
from state_replies import replies

if sys.version_info < (3,):
    maketrans = string.maketrans
else:
    maketrans = str.maketrans


yes_words = set([x.strip() for x in open('../resources/yes_words.txt').readlines()])
no_words = set([x.strip() for x in open('../resources/no_words.txt').readlines()])
loss_words = set([x.strip() for x in open('../resources/loss_description_wakewords.txt').readlines()])
exterior_words = set([x.strip() for x in open('../resources/exterior_wakewords.txt').readlines()])
interior_words = set([x.strip() for x in open('../resources/interior_wakewords.txt').readlines()])


def text_to_word_sequence(text,
                          filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n',
                          lower=True, split=" "):
    if lower:
        text = text.lower()

    if sys.version_info < (3,):
        if isinstance(text, unicode):
            translate_map = dict((ord(c), unicode(split)) for c in filters)
            text = text.translate(translate_map)
        elif len(split) == 1:
            translate_map = maketrans(filters, split * len(filters))
            text = text.translate(translate_map)
        else:
            for c in filters:
                text = text.replace(c, split)
    else:
        translate_dict = dict((c, split) for c in filters)
        translate_map = maketrans(translate_dict)
        text = text.translate(translate_map)

    seq = text.split(split)
    return [i for i in seq if i]

def get_chat_intent(text):
    orig_text = text
    text = text_to_word_sequence(text)
    if any(w in text for w in ['file', 'report', 'make']):
        if verify_policy_number(orig_text)['response'] == 'ok':
            return 'file_claim_policy_number'
        return 'file_claim'
    elif any(w in text for w in ['check', 'status']):
        return 'check_status'
    else:
        return 'other'


def verify_policy_number(text):
    number = "".join(re.findall(r'\d', text))
    if number == "":
        return {'response': 'non_numeric', 'reply': replies['f1_1']}
    try:
        return {'response': 'ok', 'value': number[-6:], 'reply': replies['3']}
    except:
        return {'replies': 'digit_unmatched', 'reply': replies['f1_2']}


def verify_phone_number(text):
    pattern = r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'
    numbers = re.findall(pattern, text)
    try:
        number =  re.sub("[^0-9]", "",  numbers[0])
        if len(number) == 10:
            return {'response': 'valid', 'value': number, 'reply': replies['4']}
        elif len(number) == 7:
            return {'response': 'area_code_missing', 'value': number, 'reply':  'Ok. And the area code?'}
        else:
            return {'response': 'not_valid', 'reply':  'This doesn\'t seem like a valid number. Please provide your phone number with area code'}
    except:
        return {'response': 'not_valid', 'reply':  'This doesn\'t seem like a valid number. Please provide your phone number with area code'}

def verify_phone_number_2(text):
    ans = dwrap.parse_phone_number(text)
    if len(ans) > 0:
        ret =  ans[0]['value']['value']
        if len(ret) == 7:
            return 'area_code_needed', ret
        else:
            return 'valid', ret
    else:
        return 'not_found'

def get_power_loss_duration(text):
    ans = dwrap.parse_duration(text)
    if len(ans) > 0:
        return ans[0]['value']
    else:
        return 'not_found'

def get_loss_date(text):
    ans = dwrap.parse_time(text)
    if len(ans) > 0:
        for v in ans:
            if 'grain' in v['value'] and v['value']['grain'] == 'day':
                return v['value']['value']
        return ans[0]['value']['value']
    else:
        return 'not_found'

def verify_email_address(text):
    match = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    if match == []:
        return 'not_valid'
    return 'valid'

def verify_name(input_text, golden_text):
    score =  fuzz.token_sort_ratio(input_text, golden_text)
    if score > 50:
        return True, score
    else:
        return False, 100-score


def get_power_loss(text):
    text = text_to_word_sequence(text)
    if any(w in text for w in yes_words):
        return 'yes'
    if any(w in text for w in no_words):
        return 'no'
    return 'not_valid'


def get_food_spoilage(text):
    text = text_to_word_sequence(text)
    if any(w in text for w in yes_words):
        return 'yes'
    if any(w in text for w in no_words):
        return 'no'
    return 'not_valid'

def get_food_spoilage_estimate(text):
    ans = dwrap.parse_money(text)
    if len(ans) > 0:
        return ans[0]['value']
    else:
        return 'not_found'


def get_home_livable(text):
    text = text_to_word_sequence(text)
    if any(w in text for w in yes_words):
        return 'yes'
    if any(w in text for w in no_words):
        return 'no'
    return 'not_valid'

def wake_word(text, type_set):
    wdict, counter = {}, 0
    text = text_to_word_sequence(text)
    for word in text:
        if word in type_set:
            counter += 1
            if word in wdict: 
                wdict[word] += 1
            else:
                wdict[word] = 1
    return wdict, counter/(1.*len(text))

def get_loss(text, thresh=0.05):
    loss_dict, loss_confidence = wake_word(text, loss_words)
    exterior_dict, exterior_confidence = wake_word(text, exterior_words)
    interior_dict, interior_confidence = wake_word(text, interior_words)

    rdict =  {}
    if loss_confidence >= thresh:
        rdict['loss'] =  { 
                        'words': loss_dict,
                         'confidence': loss_confidence
                }
    if exterior_confidence >= thresh:
        rdict['exterior'] =  {
                        'words': exterior_dict,
                        'confidence': exterior_confidence
            }
    if interior_confidence >= thresh:
        rdict['interior'] = {
                        'words': interior_dict,
                        'confidence': interior_confidence
            }
    return rdict


import requests
url = 'https://api.wit.ai/message/'
access_token = 'ER5724T3JX63YAYI7RPDNM6IXRZGSN3F'

def get_location(text):
    params = {
        'q': text,
        'access_token': access_token
    }
    response = requests.get(url, params=params).json()
    if 'location' in response['entities']:
        ret = []
        for i in  response['entities']['location']:
            ret.append(i['value'])
        return ' '.join(ret)
    return None


def get_name(text):
    params = {
        'q': text,
        'access_token': access_token
    }
    response = requests.get(url, params=params).json()
    if 'contact' in response['entities']:
        ret = []
        for i in response['entities']['contact']:
            ret.append(i['value'])
        return ' '.join(ret)
    return None


def get_initial_intent(text):
    params = {
        'q': text,
        'access_token': access_token
    }
    response = requests.get(url, params=params).json()
    try:
        return response['entities']['intent'][0]['value']
    except:
        return response





