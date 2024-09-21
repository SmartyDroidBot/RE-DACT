import ast, os
from PIL import Image, ImageDraw
from .agents import config_list
from .agents import TextRedactionAgents, ImageRedactionAgents, user_proxy
from .guardrails import guardrail_proper_nouns, guardrail_proper_nouns_list, guardrail_emails
from .utils import azure_image_ocr, export_redacted_image
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

    def redact_text(self, text):
        redacted_list_from_agent = self.assistant(text, aggregation_strategy="first")
        redacted_text_from_agent = text
        redacted_list = []
        for entity in redacted_list_from_agent:
            if self.degree == 0:
                if entity['entity_group'] in self.degree0_list:
                    redacted_list += entity['word'].strip().split()
            elif self.degree == 1:
                if entity['entity_group'] in self.degree0_list + self.degree1_list:
                    redacted_list += entity['word'].strip().split()
            elif self.degree == 2:
                if entity['entity_group'] in self.degree0_list + self.degree1_list + self.degree2_list:
                    redacted_list += entity['word'].strip().split()
        redacted_list = list(set(redacted_list))
        for word in redacted_list:
            redacted_text_from_agent = redacted_text_from_agent.replace(word, '*' + word + '*')
                
        # Return chat history
        agent_speech = []
        agent_speech.append('<h4>' + 'assistant' + '</h4>')
        agent_speech.append('<p>' + str(redacted_text_from_agent) + '</p>')
        
        # Guardrails
        if self.guardrail_toggle:        
            redacted_text_no_proper_nouns = guardrail_proper_nouns(redacted_text_from_agent)
            redacted_text_no_phonesEmailsDates = guardrail_emails(redacted_text_no_proper_nouns)
            redacted_text = redacted_text_no_phonesEmailsDates

            agent_speech.append('<h4>' + 'guardrail: redacting proper nouns' + '</h4>')
            agent_speech.append('<p>' + redacted_text_no_proper_nouns + '</p>')
            agent_speech.append('<h4>' + 'guardrail: redacting emails' + '</h4>')
            agent_speech.append('<p>' + redacted_text_no_phonesEmailsDates + '</p>')
        else:
            redacted_text = redacted_text_from_agent     

        return redacted_text, agent_speech


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
    
    def redact_image(self, image):
        result = azure_image_ocr(image)

        redacted_list_from_agent = self.assistant(result.content, aggregation_strategy="first")
        redacted_list = []
        for entity in redacted_list_from_agent:
            if self.degree == 0:
                if entity['entity_group'] in self.degree0_list:
                        redacted_list += entity['word'].strip().split()
            elif self.degree == 1:
                if entity['entity_group'] in self.degree0_list + self.degree1_list:
                        redacted_list += entity['word'].strip().split()
            elif self.degree == 2:
                if entity['entity_group'] in self.degree0_list + self.degree1_list + self.degree2_list:
                        redacted_list += entity['word'].strip().split()
        redacted_list = list(set(redacted_list))

        # Return chat history
        agents_speech = []
        agents_speech.append('<h4>' + 'assistant' + '</h4>')
        agents_speech.append('<p>' + str(redacted_list) + '</p>')
        
        # Guardrails are called only for last degree
        if self.guardrail_toggle:
            redacted_text_no_proper_nouns = guardrail_proper_nouns_list(result.content)
            redacted_list = list(set(redacted_list + redacted_text_no_proper_nouns))

            agents_speech.append('<h4>' + 'guardrail: redacting proper nouns' + '</h4>')
            agents_speech.append('<p>' + str(redacted_text_no_proper_nouns) + '</p>')

        # Extract redacted words and their coordinates
        redacted_cords = []
        for page in result.pages:
                for word in page.words:
                        for redacted_word in redacted_list:
                            if redacted_word in word.content:
                                cords = []
                                for polygon in word.polygon:
                                    cords.append((polygon.x, polygon.y))
                                redacted_cords.append(cords)

        # Export redacted image
        output_path = export_redacted_image(image, redacted_cords)

        return output_path, agents_speech

