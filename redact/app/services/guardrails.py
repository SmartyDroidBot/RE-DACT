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

import logging
# Define Logging for redaction processes
logging.basicConfig(filename='redaction_log.txt', level=logging.INFO)

# Guardrail that redacts names
name_pattern = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b")
def redact_names(text):
    return re.sub(name_pattern, '***', text)

# Guardrail that redacts Phone Numbers
phone_pattern = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
# Function to redact phone numbers
def redact_phone_numbers(text):
    return re.sub(phone_pattern, '***', text)

# Guardrail that redacts emails
email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
# Function to redact email addresses
def redact_emails(text):
    return re.sub(email_pattern, '***', text)

# Guardrail that redacts Social Security Numbers
ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
def redact_ssns(text):
    return re.sub(ssn_pattern, '***', text)

# Guardrail that redacts addresses
address_pattern = re.compile(r"\d+\s[A-Za-z]+\s[A-Za-z]+")
# Function to redact addresses
def redact_addresses(text):
    return re.sub(address_pattern, '***', text)

# Guardrail that redacts obfuscated emails
obfuscated_email_pattern = re.compile(r"[A-Za-z0-9._%+-]+\s?at\s?[A-Za-z0-9.-]+\s?dot\s?[A-Za-z]{2,}")
# Function to redact obfuscated email addresses
def redact_obfuscated_emails(text):
    return re.sub(obfuscated_email_pattern, '***', text)

# Guadrail that redacts dates
obfuscated_date_pattern = re.compile(
    r"(?:(\d{1,2})(st|nd|rd|th)?\s?(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s?\d{4})|"
    r"(?:(\d{1,2})(st|nd|rd|th)?[-/\s](\d{1,2})[-/\s](\d{2,4}))")
# Function to redact obfuscated dates
def redact_obfuscated_dates(text):
    return re.sub(obfuscated_date_pattern, '***', text)

# Guardrail to flag gibberish
gibberish_pattern = re.compile(r"\b(?:[^\s\w\d]{5,}|[a-zA-Z]{5,}\d+|[a-zA-Z]{10,}|[^a-zA-Z\s]{3,})\b")
# Function to redact gibberish
def redact_gibberish(text):
    return re.sub(gibberish_pattern, 'gibberish', text)


