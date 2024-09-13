import os
from django.conf import settings
import regex as re

import nltk
nltk.download('averaged_perceptron_tagger_eng')

# Guardrail that redacts proper nouns
def guardrail_proper_nouns(text):
    from nltk.tag import pos_tag

    for word in text.split(' '):
        if '*' not in word:
            tag = pos_tag([word])[0][1]
            if tag == 'NNP':
                text = text.replace(word, '*' + word + '*')

    return text

# Guardrail that redacts proper nouns and returns a list
def guardrail_proper_nouns_list(text):
    from nltk.tag import pos_tag

    redacted_words = []
    for word in text.split(' '):
        if '*' not in word:
            tag = pos_tag([word])[0][1]
            if tag == 'NNP':
                redacted_words.append(word)

    return redacted_words

# Guardrail that redacts capitalized words
def guardrail_capitalized_words(text):
    def replace_match(match):
        word = match.group(0)
        return f'*{word}*'

    text = re.sub(r'(?<!^)(?<!\*)\b[A-Z][a-zA-Z]*\b(?!\*)', replace_match, text)

    return text
