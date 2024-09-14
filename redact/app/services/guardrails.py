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
# Guardrails to redact names, emails,  dates,etc and gibberish
import logging

# Define Logging for redaction processes
logging.basicConfig(filename='redaction_log.txt', level=logging.INFO)

# Regex Patterns for Redaction
name_pattern = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b")
phone_pattern = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
address_pattern = re.compile(r"\d+\s[A-Za-z]+\s[A-Za-z]+")
obfuscated_email_pattern = re.compile(r"[A-Za-z0-9._%+-]+\s?at\s?[A-Za-z0-9.-]+\s?dot\s?[A-Za-z]{2,}")
obfuscated_date_pattern = re.compile(
    r"(?:(\d{1,2})(st|nd|rd|th)?\s?(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s?\d{4})|"
    r"(?:(\d{1,2})(st|nd|rd|th)?[-/\s](\d{1,2})[-/\s](\d{2,4}))"
)
gibberish_pattern = re.compile(r"\b(?:[^\s\w\d]{5,}|[a-zA-Z]{5,}\d+|[a-zA-Z]{10,}|[^a-zA-Z\s]{3,})\b")

# List of terms to exclude from redaction
excluded_terms = ['Corp', 'Inc', 'Company']

# Function to redact names
def redact_names(text):
    return re.sub(name_pattern, '***', text)

# Function to redact phone numbers
def redact_phone_numbers(text):
    return re.sub(phone_pattern, '***', text)

# Function to redact email addresses
def redact_emails(text):
    return re.sub(email_pattern, '***', text)

# Function to redact Social Security Numbers (SSNs)
def redact_ssns(text):
    return re.sub(ssn_pattern, '***', text)

# Function to redact addresses
def redact_addresses(text):
    return re.sub(address_pattern, '***', text)

# Function to redact obfuscated email addresses
def redact_obfuscated_emails(text):
    return re.sub(obfuscated_email_pattern, '***', text)

# Function to redact obfuscated dates
def redact_obfuscated_dates(text):
    return re.sub(obfuscated_date_pattern, '***', text)

# Function to redact gibberish
def redact_gibberish(text):
    return re.sub(gibberish_pattern, 'gibberish', text)

# Function to exclude certain terms from redaction
def exclude_terms(text):
    for term in excluded_terms:
        text = re.sub(f"\\b{term}\\b", term, text)
    return text

# Main redaction function
def redact_personal_info(text):
    # Apply redaction functions
    redacted_text = redact_names(text)
    redacted_text = redact_phone_numbers(redacted_text)
    redacted_text = redact_emails(redacted_text)
    redacted_text = redact_ssns(redacted_text)
    redacted_text = redact_addresses(redacted_text)
    redacted_text = redact_obfuscated_emails(redacted_text)
    redacted_text = redact_obfuscated_dates(redacted_text)
    redacted_text = redact_gibberish(redacted_text)
    redacted_text = exclude_terms(redacted_text)
    
    return redacted_text

# Process redaction
output_text = redact_personal_info(input_text)

# Print the redacted text
print(output_text)
