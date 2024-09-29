from .agents import config_list
from .agents import TextRedactionAgents, ImageRedactionAgents, PDFRedactionAgents
from .guardrails import guardrail_proper_nouns, guardrail_numbers, guardrail_urls, guardrail_emails
from .db_service import uploadOutputDB
from .utils import azure_image_ocr, azure_pdf_ocr, match_regexPattern, export_redacted_image, export_redacted_pdf
from django.conf import settings

class TextRedactionService:
    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = 0
        # Temporary: Toggling guardrails on for 3rd degree only
        if degree == 2 and guardrail_toggle:
            self.guardrail_toggle = 1

        self.assistant = TextRedactionAgents(degree).assistant
        self.degree0_list = TextRedactionAgents(degree).degree0_list
        self.degree1_list = TextRedactionAgents(degree).degree1_list
        self.degree2_list = TextRedactionAgents(degree).degree2_list

    def redact_text(self, text, regexPattern, wordsToRemove=[]):
        word_list = text.split()
        redacted_list = []
        redacted_list_from_agent = [] + [j for i in wordsToRemove for j in i.split()]
        output_db_list = [] # Storing outputs for improving models

        raw_redacted_list_from_agent = self.assistant(text, aggregation_strategy="first")
        for entity in raw_redacted_list_from_agent:
            if self.degree == 0:
                if entity['entity_group'] in self.degree0_list:
                    redacted_list_from_agent += entity['word'].strip().split()
            elif self.degree == 1:
                if entity['entity_group'] in self.degree0_list + self.degree1_list:
                    redacted_list_from_agent += entity['word'].strip().split()
            elif self.degree == 2:
                if entity['entity_group'] in self.degree0_list + self.degree1_list + self.degree2_list:
                    redacted_list_from_agent += entity['word'].strip().split()
            # Appending to Output DB List
            output_db_list.append({
                'word': entity['word'],
                'label': entity['entity_group']
            })

        redacted_list_from_agent = list(set(redacted_list_from_agent))
        uploadOutputDB(output_db_list)

        # Match regex pattern given by user
        regex_matches = match_regexPattern(text, regexPattern)
        redacted_list_from_agent = list(set(redacted_list_from_agent + regex_matches))
                
        # Return chat history
        agents_speech = []
        agents_speech.append('<h4>' + 'assistant' + '</h4>')
        agents_speech.append('<p>Redacting words: ' + str(redacted_list_from_agent) + '</p>')
        
        # Guardrails
        if self.guardrail_toggle:        
            redacted_list_no_proper_nouns = guardrail_proper_nouns(word_list)
            redacted_list_no_numbers = guardrail_numbers(word_list)
            redacted_list_no_urls = guardrail_urls(word_list)
            redacted_list_no_emails = guardrail_emails(word_list)
            redacted_list = list(set(redacted_list_from_agent + redacted_list_no_proper_nouns + redacted_list_no_numbers + redacted_list_no_urls + redacted_list_no_emails))

            agents_speech.append('<h4>' + 'guardrail: redacting proper nouns' + '</h4>')
            agents_speech.append('<p>Redacting Proper Nouns: ' + str(redacted_list_no_proper_nouns) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting numbers' + '</h4>')
            agents_speech.append('<p>Redacting Numbers: ' + str(redacted_list_no_numbers) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting urls' + '</h4>')
            agents_speech.append('<p>Redacting URLs: ' + str(redacted_list_no_urls) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting emails' + '</h4>')
            agents_speech.append('<p>Redacting Emails: ' + str(redacted_list_no_emails) + '</p>')
        else:
            redacted_list = redacted_list_from_agent  
        redacted_list = sorted(redacted_list, key=len, reverse=True)

        # Redact text
        redacted_text = text
        for redacted_word in redacted_list:
            # Removing single characters from redacted words but not numbers
            if len(redacted_word.strip()) <= 1 and not redacted_word.strip().isnumeric():
                continue
            else:
                redacted_text = redacted_text.replace(redacted_word.strip(), '*' + '█' * len(redacted_word.strip()) + '*')

        return redacted_text, agents_speech


class ImageRedactionService:
    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = 0
        # Temporary: Toggling guardrails on for 3rd degree only
        if degree == 2 and guardrail_toggle:
            self.guardrail_toggle = 1

        self.assistant = ImageRedactionAgents(degree).assistant
        self.degree0_list = ImageRedactionAgents(degree).degree0_list
        self.degree1_list = ImageRedactionAgents(degree).degree1_list
        self.degree2_list = ImageRedactionAgents(degree).degree2_list
    
    def redact_image(self, image, regexPattern, wordsToRemove=[]):
        result = azure_image_ocr(image)
        word_list = result.content.split()
        redacted_list = []
        output_db_list = [] # Storing outputs for improving models

        raw_redacted_list_from_agent = self.assistant(result.content, aggregation_strategy="first")
        redacted_list_from_agent = [] + [j for i in wordsToRemove for j in i.split()]
        for entity in raw_redacted_list_from_agent:
            if self.degree == 0:
                if entity['entity_group'] in self.degree0_list:
                        redacted_list_from_agent += entity['word'].strip().split()
            elif self.degree == 1:
                if entity['entity_group'] in self.degree0_list + self.degree1_list:
                        redacted_list_from_agent += entity['word'].strip().split()
            elif self.degree == 2:
                if entity['entity_group'] in self.degree0_list + self.degree1_list + self.degree2_list:
                        redacted_list_from_agent += entity['word'].strip().split()
            # Appending to Output DB List
            output_db_list.append({
                'word': entity['word'],
                'label': entity['entity_group']
            })

        redacted_list_from_agent = list(set(redacted_list_from_agent))
        uploadOutputDB(output_db_list)

        # Match regex pattern given by user
        regex_matches = match_regexPattern(result.content, regexPattern)
        redacted_list_from_agent = list(set(redacted_list_from_agent + regex_matches))

        # Return chat history
        agents_speech = []
        agents_speech.append('<h4>' + 'assistant' + '</h4>')
        agents_speech.append('<p>Redacting words: ' + str(redacted_list_from_agent) + '</p>')
        
        # Guardrails are called only for last degree
        if self.guardrail_toggle:
            redacted_list_no_proper_nouns = guardrail_proper_nouns(word_list)
            redacted_list_no_numbers = guardrail_numbers(word_list)
            redacted_list_no_urls = guardrail_urls(word_list)
            redacted_list_no_emails = guardrail_emails(word_list)
            redacted_list = list(set(redacted_list_from_agent + redacted_list_no_proper_nouns + redacted_list_no_numbers + redacted_list_no_urls + redacted_list_no_emails))

            agents_speech.append('<h4>' + 'guardrail: redacting proper nouns' + '</h4>')
            agents_speech.append('<p>Redacting Proper Nouns: ' + str(redacted_list_no_proper_nouns) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting numbers' + '</h4>')
            agents_speech.append('<p>Redacting Numbers: ' + str(redacted_list_no_numbers) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting urls' + '</h4>')
            agents_speech.append('<p>Redacting URLs: ' + str(redacted_list_no_urls) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting emails' + '</h4>')
            agents_speech.append('<p>Redacting Emails: ' + str(redacted_list_no_emails) + '</p>')
        else:
            redacted_list = redacted_list_from_agent
        redacted_list = sorted(redacted_list, key=len, reverse=True)

        # Extract redacted words and their coordinates
        redacted_cords = []
        for page in result.pages:
            for word in page.words:
                for redacted_word in redacted_list:
                    # Removing single characters from redacted words but not numbers
                    if len(redacted_word.strip()) <= 1 and not redacted_word.strip().isnumeric():
                        continue
                    elif redacted_word in word.content or redacted_word.strip() in word.content.strip():
                        cords = []
                        for polygon in word.polygon:
                            cords.append((polygon.x, polygon.y))
                        redacted_cords.append(cords)

        # Export redacted image
        output_path = export_redacted_image(image, redacted_cords)

        return output_path, agents_speech
    
    
class PDFRedactionService:
    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = 0
        # Temporary: Toggling guardrails on for 3rd degree only
        if degree == 2 and guardrail_toggle:
            self.guardrail_toggle = 1

        self.assistant = PDFRedactionAgents(degree).assistant
        self.degree0_list = PDFRedactionAgents(degree).degree0_list
        self.degree1_list = PDFRedactionAgents(degree).degree1_list
        self.degree2_list = PDFRedactionAgents(degree).degree2_list
    
    def redact_pdf(self, pdf, regexPattern, wordsToRemove=[]):
        result = azure_pdf_ocr(pdf)
        word_list = result.content.split()
        redacted_list = []
        output_db_list = [] # Stores outputs for improvingm models
        redacted_list_from_agent = [] + [j for i in wordsToRemove for j in i.split()]

        for page in result.pages:
            raw_redacted_list_from_agent_page = self.assistant(" ".join([line.content for line in page.lines]), aggregation_strategy="first")
            for entity in raw_redacted_list_from_agent_page:
                if self.degree == 0:
                    if entity['entity_group'] in self.degree0_list:
                        redacted_list_from_agent += entity['word'].strip().split()
                elif self.degree == 1:
                    if entity['entity_group'] in self.degree0_list + self.degree1_list:
                        redacted_list_from_agent += entity['word'].strip().split()
                elif self.degree == 2:
                    if entity['entity_group'] in self.degree0_list + self.degree1_list + self.degree2_list:
                        redacted_list_from_agent += entity['word'].strip().split()
                # Appending to Output DB List
                output_db_list.append({
                    'word': entity['word'],
                    'label': entity['entity_group']
                })

        redacted_list_from_agent = list(set(redacted_list_from_agent))
        uploadOutputDB(output_db_list)

        redacted_list_from_agent = list(set(redacted_list_from_agent))

        # Match regex pattern given by user
        regex_matches = match_regexPattern(result.content, regexPattern)
        redacted_list_from_agent = list(set(redacted_list_from_agent + regex_matches))

        # Return chat history
        agents_speech = []
        agents_speech.append('<h4>' + 'assistant' + '</h4>')
        agents_speech.append('<p>Redacting words: ' + str(redacted_list_from_agent) + '</p>')
        
        # Guardrails are called only for last degree
        if self.guardrail_toggle:
            redacted_list_no_proper_nouns = guardrail_proper_nouns(word_list)
            redacted_list_no_numbers = guardrail_numbers(word_list)
            redacted_list_no_urls = guardrail_urls(word_list)
            redacted_list_no_emails = guardrail_emails(word_list)
            redacted_list = list(set(redacted_list_from_agent + redacted_list_no_proper_nouns + redacted_list_no_numbers + redacted_list_no_urls + redacted_list_no_emails))

            agents_speech.append('<h4>' + 'guardrail: redacting proper nouns' + '</h4>')
            agents_speech.append('<p>Redacting Proper Nouns: ' + str(redacted_list_no_proper_nouns) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting numbers' + '</h4>')
            agents_speech.append('<p>Redacting Numbers: ' + str(redacted_list_no_numbers) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting urls' + '</h4>')
            agents_speech.append('<p>Redacting URLs: ' + str(redacted_list_no_urls) + '</p>')
            agents_speech.append('<h4>' + 'guardrail: redacting emails' + '</h4>')
            agents_speech.append('<p>Redacting Emails: ' + str(redacted_list_no_emails) + '</p>')
        else:
            redacted_list = redacted_list_from_agent
        redacted_list = sorted(redacted_list, key=len, reverse=True)

        # Extract redacted words and their coordinates
        redacted_cords = []
        page_dims = []
        for page in result.pages:
            page_dims.append((page.width, page.height))
            redacted_cords_page = []
            for word in page.words:
                for redacted_word in redacted_list:
                    # Removing single characters from redacted words but not numbers
                    if len(redacted_word.strip()) <= 1 and not redacted_word.strip().isnumeric():
                        continue
                    elif redacted_word in word.content or redacted_word.strip() in word.content.strip():
                        cords = []
                        for polygon in word.polygon:
                            cords.append((polygon.x, polygon.y))
                        redacted_cords_page.append(cords)
            redacted_cords.append(redacted_cords_page)

        # Export redacted PDF
        output_path = export_redacted_pdf(pdf, redacted_cords, page_dims)

        return output_path, agents_speech

