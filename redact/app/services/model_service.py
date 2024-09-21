import ast, os
import autogen
from PIL import Image, ImageDraw
from .agents import config_list
from .agents import TextRedactionAgents, ImageRedactionAgents, user_proxy
from .guardrails import guardrail_proper_nouns, guardrail_proper_nouns_list, guardrail_capitalized_words, guardrail_phonesEmailsDates
from .utils import azure_image_ocr, export_redacted_image, redact_text
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
        self.degree = degree
        self.guardrail_toggle = guardrail_toggle

         # Define the chat outline
        self.chat_outline = {
            'message': '',
        }

        self.image_assistant, self.evaluation = ImageRedactionAgents(degree).image_assistant, TextRedactionAgents(degree).evaluation
        self.user_proxy = user_proxy
    
    def redact_image(self, image):
        result = azure_image_ocr(image)

        global conversation_state
        conversation_state = 1
        speakers = []

        def image_redact_selection_func(speaker: autogen.AssistantAgent, groupchat: autogen.GroupChat):
            global conversation_state
            if speaker == self.user_proxy and conversation_state == 1:
                conversation_state += 1
                speakers.append(self.image_assistant.name)
                return self.image_assistant
            elif speaker == self.image_assistant and conversation_state == 2:
                conversation_state += 1
                speakers.append(self.evaluation.name)
                return self.evaluation
            elif speaker == self.evaluation and conversation_state == 3:
                conversation_state += 1
                speakers.append(self.image_assistant.name)
                return self.image_assistant

        # Update chat outline with user-provided text
        self.chat_outline['message'] = result.content

        # Define the GroupChat and GroupChatManager
        image_redaction_chat = autogen.GroupChat(
            agents=[self.user_proxy, self.image_assistant, self.evaluation],
            speaker_selection_method=image_redact_selection_func,
            messages=[],
            max_round=4 
        )

        image_redaction_manager = autogen.GroupChatManager(
            groupchat=image_redaction_chat, llm_config=config_list
        )

        # Initiate the chat
        image_redaction_chats = self.user_proxy.initiate_chat(
            image_redaction_manager,
            message=self.chat_outline['message']
        )

        # Return chat history
        agents_speech = []
        for i, chat in enumerate(speakers):
            agents_speech.append('<h4>' + speakers[i] + '</h4>')
            agents_speech.append('<p>' + image_redaction_chats.chat_history[i+1]['content'] + '</p>')

        # Extract redacted words and their coordinates
        redacted_text = image_redaction_chats.chat_history[-1]['content']
        redacted_text = ast.literal_eval(redacted_text)
        redacted_words = []
        for text in redacted_text:
            for word in str(text).split(' '):
                if len(word) > 3:
                    redacted_words.append(word)
        
        # Guardrails are called only for last degree
        if self.guardrail_toggle:
            redacted_text_no_proper_nouns = guardrail_proper_nouns_list(image_redaction_chats.chat_history[-1]['content'])
            redacted_words = list(set(redacted_words + redacted_text_no_proper_nouns))

            agents_speech.append('<h4>' + 'guardrail: redacting proper nouns' + '</h4>')
            agents_speech.append('<p>' + str(redacted_text_no_proper_nouns) + '</p>')

        # Extract redacted words and their coordinates
        redacted_cords = []
        for page in result.pages:
                for word in page.words:
                        for redacted_word in redacted_words:
                            if redacted_word in word.content:
                                cords = []
                                for polygon in word.polygon:
                                    cords.append((polygon.x, polygon.y))
                                redacted_cords.append(cords)

        # Export redacted image
        output_path = export_redacted_image(image, redacted_cords)

        return output_path, agents_speech

