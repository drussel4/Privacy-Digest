import json
import re
import pandas as pd

# Identify key terms and phrases
terms = {
    'phrases':[
        'seek to',
        'strive to',
        'research purposes',
        'purposes necessary to provide products and services',
        'retain your data for as long as necessary',
    ],
    'transformations':[
        'anonymiz*',
        'aggregat*',
    ],
    'PII':[
        'name*',
        'phone*',
        'email addr*',
        'username*',
        'password*',
        'credit card*',
        'dedit card*',
        'card numb*',
        'bank acc*',
        'physical addr*',
        'street addr*',
        'home addr*',
        'zip*',
        'geoloc*',
        'date of birth',
        'dob',
        'birthda*',
        'birth da*',
        'purchase hist*',
        'transaction hist*',
    ],
}

# Import LIWC Lexicon
with open('../data/liwc_lexicon_reduced.json') as f:
    liwc_lexicon = json.load(f)

# Settings for liwc evaluation
skip_terms = ['if', 'or']
lookback_steps = 2

# Check for matches with key terms per category; strict/lenient regex
def score_text(text):
    
    # print('Beginning score_text()')

    category_match_dict = {}
    keyword_match_list = []
    matches_count = 0
    for category in terms.keys():
        category_match_list = []
        for keyword in terms[category]:
            if keyword[-1] == '*': # WILDCARD, LENIENT SEARCH
                boundaries = ('', '[A-z]?')
            else: # STRICT SEARCH
                boundaries = ('', '')
            keyword = keyword.replace('*', '')
            re_str = '{}{}{}'.format(boundaries[0], keyword.lower(), boundaries[1])
            try:
                match = re.search(re_str, text, re.IGNORECASE)
            except Exception as e:
                print('Encountered error parsing text "{}" for keyword "{}": {}'.format(text, keyword, e))
                raise e
            
            if match is not None:
                category_match_list.append(keyword)
                if keyword not in keyword_match_list:
                    keyword_match_list.append(keyword)
                matches_count += 1

        if len(category_match_list) > 0:
            category_match_dict[category] = category_match_list
    
    return {
        'categories_ct':len(category_match_dict.keys()),
        'keywords_ct':matches_count,
        'categories':', '.join(sorted(list(category_match_dict.keys()))),
        'keywords':', '.join(sorted(keyword_match_list)),
        'keywords_list':keyword_match_list,
        }

### Run score_text() for each site's privacy policy
for site in ['Spotify', 'Apple Music', 'MusicLeague']:
    with open(f'{site}.json') as f:
        site_privacy_policy = json.load(f)
    lexicon_score = score_text(site_privacy_policy)
    print(f"{site} results: {lexicon_score['keywords_ct']} keywords in {lexicon_score['categories_ct']} categories: {lexicon_score['keywords']}")
    with open(f'lexicon_{site}.json', 'w') as fp:
        json.dump(lexicon_score, fp, default=str)
raise Exception

'''
Spotify results: 11 keywords in 2 categories: aggregat, card numb, credit card, date of birth, email addr, name, password, phone, street addr, username, zip
Apple Music results: 4 keywords in 2 categories: aggregat, email addr, name, phone
MusicLeague results: 10 keywords in 2 categories: aggregat, anonymiz, credit card, email addr, name, password, phone, physical addr, transaction hist, username
'''

# Score policy for vagueness
def score_vagueness(text):
    results = {}
    tokens = text.lower().split(' ') 
    # with open('tokens.json', 'w') as fp:
    #     json.dump(tokens, fp, default=str)
    # raise Exception
    results = {
        'Certain':{'count':0, 'kw':[]},
        'Tentat':{'count':0, 'kw':[]},
    }
    for cat in liwc_lexicon.keys():
        if cat in ['Certain', 'Tentat']:
            for kw in liwc_lexicon[cat]:
                
                # Skip noisy terms (e.g., "if" is a poor predictor of "Tentat")
                if kw in skip_terms:
                    continue
                
                if kw[-1] == '*': # WILDCARD, LENIENT SEARCH
                    boundaries = ('', '[A-z]?')
                else: # STRICT SEARCH
                    boundaries = ('', '')
                kw = kw.replace('*', '')
                re_str = '{}{}{}'.format(boundaries[0], kw, boundaries[1])
                                
                # Regex with tokens
                for i, token in enumerate(tokens):
                    valid = True
                    match = re.search(re_str, token, re.IGNORECASE)
                    if match is not None:
                        
                        # Reverse assignment in instances where a matching term was preceeded by a negator
                        # (e.g., "not sure" and "not entirely sure" +1 to Tentat, while "sure" is within cat: Certain)
                        for j in range(1, lookback_steps+1):
                            if i-j >= 0:
                                prior_token = tokens[i-j]
                                if prior_token in liwc_lexicon['Negate']:
                                    valid = False
                                    break
                        
                        if valid:
                            results[cat]['count'] += 1
                            results[cat]['kw'].append(kw)
                        else:
                            if cat == 'Certain':
                                results['Tentat']['count'] += 1
                                results['Tentat']['kw'].append('{}... {}'.format(prior_token, kw))
                            elif cat == 'Tentat':
                                results['Certain']['count'] += 1
                                results['Certain']['kw'].append('{}... {}'.format(prior_token, kw))
        
    # Skepticism (Tentat) ratio
    if results['Tentat']['count'] == 0:
        results['ratio'] = 0.0
    else:
        results['ratio'] = results['Tentat']['count'] / (results['Tentat']['count'] + results['Certain']['count'])
    
    return results

# test = 'Blatantly something I probably maybe want to get, is it though? I am certain it is. And yet I am not sure it is.'
# vague_results = score_vagueness(test)
# print(f"test results: Certain: {vague_results['Certain']['count']}, Tentative: {vague_results['Tentat']['count']} (ratio: {vague_results['ratio']})")
# with open(f'vague_test.json', 'w') as fp:
#     json.dump(vague_results, fp, default=str)
# raise Exception

### Run score_vagueness() for each site's privacy policy
for site in ['Spotify', 'Apple Music', 'MusicLeague']:
    with open(f'{site}.json') as f:
        site_privacy_policy = json.load(f)
    vague = score_vagueness(site_privacy_policy)
    print(f"{site} results: Certain: {vague['Certain']['count']}, Tentative: {vague['Tentat']['count']} (ratio: {vague['ratio']})")
    with open(f'vague_{site}.json', 'w') as fp:
        json.dump(vague, fp, default=str)

'''
Spotify results: Certain: 138, Tentative: 95 (ratio: 0.40772532188841204)
Apple Music results: Certain: 46, Tentative: 58 (ratio: 0.5576923076923077)
MusicLeague results: Certain: 60, Tentative: 66 (ratio: 0.5238095238095238)

Spotify results: Certain: 93, Tentative: 104 (ratio: 0.5279187817258884)
Apple Music results: Certain: 52, Tentative: 56 (ratio: 0.5185185185185185)
MusicLeague results: Certain: 50, Tentative: 71 (ratio: 0.5867768595041323)

'''