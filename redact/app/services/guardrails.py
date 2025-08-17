import os
from django.conf import settings
import regex as re

import nltk
nltk.download('averaged_perceptron_tagger_eng')

# Guardrail that redacts proper nouns
def guardrail_proper_nouns(word_list):
    from nltk.tag import pos_tag
    
    redacted_list = []
    for word in word_list:
        word = word.strip()
        if word:
            tag = pos_tag([word])[0][1]
            if tag == 'NNP':
                redacted_list.append(word)

    return list(set(redacted_list))

# Guardrail that redacts numbers
def guardrail_numbers(word_list):
    patterns = {
        "numbers": re.compile(r"\b\d+[\d.,-]*\b"),
    }

    redacted_list = []
    for pattern in patterns.values():
        matches = pattern.findall(' '.join(word_list))
        for match in matches:
            match_text = ''.join(match).strip()
            if match_text:
                redacted_list.append(match_text)
    
    return redacted_list

# Guardrail that redacts URLs
def guardrail_urls(word_list):
    patterns = {
        "urls": re.compile(r'(?:https?://)?(?:www\.)?([\w.-]+\.\w+)'),
    }

    redacted_list = []
    for pattern in patterns.values():
        matches = pattern.findall(' '.join(word_list))
        for match in matches:
            match_text = ''.join(match).strip()
            if match_text:
                redacted_list.append(match_text)
    
    return redacted_list

# Guardrail that redacts emails
def guardrail_emails(word_list):
    patterns = {
        "email": re.compile(r"(?<!\*)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b(?!\*)"),
        "obfuscated_email": re.compile(r"(?<!\*)[A-Za-z0-9._%+-]+\s?at\s?[A-Za-z0-9.-]+\s?dot\s?[A-Za-z]{2,}(?!\*)"),
    }

    redacted_list = []
    for pattern in patterns.values():
        matches = pattern.findall(' '.join(word_list))
        for match in matches:
            match_text = ''.join(match).strip()
            if match_text:
                redacted_list.append(match_text)
    
    return redacted_list
