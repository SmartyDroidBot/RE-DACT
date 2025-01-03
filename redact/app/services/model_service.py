import ast, os
import autogen
from PIL import Image, ImageDraw
from .agents import config_list
from .agents import TextRedactionAgents, ImageRedactionAgents, user_proxy
from .guardrails import guardrail_proper_nouns, guardrail_proper_nouns_list, guardrail_capitalized_words, guardrail_phonesEmailsDates
from .utils import azure_image_ocr, export_redacted_image
from django.conf import settings

class TextRedactionService:
    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = guardrail_toggle

        # Define the chat outline
        self.chat_outline = {
            'message': '',
        }

        self.text_assistant, self.evaluation = TextRedactionAgents(self.degree).text_assistant, TextRedactionAgents(self.degree).evaluation
        self.user_proxy = user_proxy

    def redact_text(self, text):
        global conversation_state
        conversation_state = 1
        speakers = []

        def text_redact_selection_func(speaker: autogen.AssistantAgent, groupchat: autogen.GroupChat):
            global conversation_state
            if speaker == self.user_proxy and conversation_state == 1:
                conversation_state += 1
                speakers.append(self.text_assistant.name)
                return self.text_assistant
            elif speaker == self.text_assistant and conversation_state == 2:
                conversation_state += 1
                speakers.append(self.evaluation.name)
                return self.evaluation
            elif speaker == self.evaluation and conversation_state == 3:
                conversation_state += 1
                speakers.append(self.text_assistant.name)
                return self.text_assistant

        # Update chat outline with user-provided text
        self.chat_outline['message'] = text

        # Define the GroupChat and GroupChatManager
        text_redaction_chat = autogen.GroupChat(
            agents=[self.user_proxy, self.text_assistant, self.evaluation],
            speaker_selection_method=text_redact_selection_func,
            messages=[],
            max_round=4
        )

        text_redaction_manager = autogen.GroupChatManager(
            groupchat=text_redaction_chat, llm_config=config_list
        )

        # Initiate the chat
        text_redaction_chats = self.user_proxy.initiate_chat(
            text_redaction_manager,
            message=self.chat_outline['message']
        )

        redacted_text_from_agent = text_redaction_chats.chat_history[-1]['content']
        redacted_text = ''

        # Return chat history
        agent_speech = []
        for i, chat in enumerate(speakers):
            agent_speech.append('<h4>' + speakers[i] + '</h4>')
            agent_speech.append('<p>' + text_redaction_chats.chat_history[i+1]['content'] + '</p>')
        
        # Guardrails are called only for last degree
        if self.guardrail_toggle:        
            redacted_text_no_proper_nouns = guardrail_proper_nouns(redacted_text_from_agent)
            redacted_text_no_capitalized_words = guardrail_capitalized_words(redacted_text_no_proper_nouns)
            redacted_text_no_phonesEmailsDates = guardrail_phonesEmailsDates(redacted_text_no_capitalized_words)
            redacted_text = redacted_text_no_phonesEmailsDates

            agent_speech.append('<h4>' + 'guardrail: redacting proper nouns' + '</h4>')
            agent_speech.append('<p>' + redacted_text_no_proper_nouns + '</p>')
            agent_speech.append('<h4>' + 'guardrail: redacting capitalized words' + '</h4>')
            agent_speech.append('<p>' + redacted_text_no_capitalized_words + '</p>')
            agent_speech.append('<h4>' + 'guardrail: redacting phones, emails, and dates' + '</h4>')
            agent_speech.append('<p>' + redacted_text_no_phonesEmailsDates + '</p>')
        else:
            redacted_text = redacted_text_from_agent     

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

