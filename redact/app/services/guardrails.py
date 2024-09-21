import os
from django.conf import settings
import regex as re

import nltk
nltk.download('averaged_perceptron_tagger_eng')

# Guardrail that redacts proper nouns
def guardrail_proper_nouns(text):
    from nltk.tag import pos_tag
    text_without_asterisks = re.sub(r'\*.*?\*', '', text)
    
    for word in text_without_asterisks.split():
        word = word.strip()
        if word:
            tag = pos_tag([word])[0][1]
            if tag == 'NNP':
                if f'*{word}*' not in text:
                    text = text.replace(word, '*' + word + '*')

    return text

# Guardrail that redacts proper nouns and returns a list of redacted words
def guardrail_proper_nouns_list(text):
    from nltk.tag import pos_tag
    text_without_asterisks = re.sub(r'\*.*?\*', '', text)

    redacted_words = []
    for word in text_without_asterisks.split():
        word = word.strip()
        if word:  
            tag = pos_tag([word])[0][1]
            if tag == 'NNP': 
                if f'*{word}*' not in text:
                    redacted_words.append(word)

    return redacted_words

# Guardrail that redacts capitalized words
def guardrail_capitalized_words(text):
    text_without_asterisks = re.sub(r'\*.*?\*', '', text)

    for word in text_without_asterisks.split():
        word = word.strip()
        if word:
            if word[0].isupper():
                if f'*{word}*' not in text:
                    text = text.replace(word, '*' + word + '*')

    return text

# Guardrail that redacts phones, emails, and dates
def guardrail_phonesEmailsDates(text):
    # Temporary skip
    return text

    text_without_asterisks = re.sub(r'\*.*?\*', '', text)

    patterns = {
        "phone": re.compile(r"(?<!\*)\b(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}(?=\s|$|[^\w])(?!\*)"),
        "email": re.compile(r"(?<!\*)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b(?!\*)"),
        "obfuscated_email": re.compile(r"(?<!\*)[A-Za-z0-9._%+-]+\s?at\s?[A-Za-z0-9.-]+\s?dot\s?[A-Za-z]{2,}(?!\*)"),
        "ssn_pattern": re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    }

    for pattern in patterns.values():
        matches = pattern.findall(text_without_asterisks)
        for match in matches:
            match_text = ''.join(match).strip()
            if match_text:
                if f'*{match_text}*' not in text:
                    text = text.replace(match_text, f"*{match_text}*")
    
    return text
