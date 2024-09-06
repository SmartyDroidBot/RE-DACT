import ast, os
import autogen
from PIL import Image, ImageDraw
from .agents import config_list
from .agents import TextRedactionAgents, ImageRedactionAgents, user_proxy
from .utils import azure_image_ocr

class TextRedactionService:
    def __init__(self, degree=0):
        # Define the chat outline
        self.chat_outline = {
            'message': '',
        }

        self.text_assistant, self.evaluation = TextRedactionAgents(degree).text_assistant, TextRedactionAgents(degree).evaluation
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

        # Return the result from the chat
        return text_redaction_chats.chat_history[-1]['content']

class ImageRedactionService:
    def __init__(self, degree=0):
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
            max_round=2
        )

        image_redaction_manager = autogen.GroupChatManager(
            groupchat=image_redaction_chat, llm_config=config_list
        )

        # Initiate the chat
        image_redaction_chats = self.user_proxy.initiate_chat(
            image_redaction_manager,
            message=self.chat_outline['message']
        )

        redacted_text = image_redaction_chats.chat_history[-1]['content']
        redacted_text = ast.literal_eval(redacted_text)
        redacted_words = []
        for text in redacted_text:
            for word in str(text).split(' '):
                if len(word) > 3:
                    redacted_words.append(word)
        redacted_words

        redacted_cords = []
        for page in result.pages:
                for word in page.words:
                        if word.content in redacted_words:
                            cords = []
                            for polygon in word.polygon:
                                cords.append((polygon.x, polygon.y))
                            redacted_cords.append(cords)

        # Load the original image
        image = Image.open(image)
        draw = ImageDraw.Draw(image)

        # For each set of coordinates, draw the black boxes
        for coord_set in redacted_cords:
            x_coords = [point[0] for point in coord_set]
            y_coords = [point[1] for point in coord_set]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            draw.rectangle([x_min, y_min, x_max, y_max], fill='black')

        output_path = r'C:/Users/shash/OneDrive/Desktop/College/SIH RE-DACT/Github_Repo/redact' + r'/media/uploads/modified_image.png'
        image.save(output_path)

        return output_path

