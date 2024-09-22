import ast, os
from .utils import image_redaction, redact_text
from django.conf import settings

class TextRedactionService:
    def __init__(self, degree=1, guardrail_toggle=1):
        self.degree = degree+1 # My degrees start from 1
        self.guardrail_toggle = guardrail_toggle

    def redact_text(self, text):
        redacted_text = redact_text(text, self.degree)
        # Return chat history
        agent_speech = []   
        return redacted_text, agent_speech


class ImageRedactionService:
    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree+1
        self.guardrail_toggle = guardrail_toggle

    def redact_image(self, image):
        output_path = image_redaction(image, self.degree)
        agents_speech = []
        return output_path, agents_speech

