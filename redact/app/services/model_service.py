import autogen
from django.conf import settings

class TextRedactionService:
    def __init__(self):
        # Initialize the configuration for the Autogen model
        self.config_list = {
            'model': 'llama3.1',
            'base_url': getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434/v1'),
            'api_key': getattr(settings, 'OLLAMA_API_KEY', 'ollama'),
        }

        # Define the ConversableAgent for text redaction
        self.text_assistant = autogen.ConversableAgent(
            'assistant',
            system_message='You are an agent designed to redact personal information from any text provided to you.'
                           'Your task is to identify and replace any personal information with stars (**).'
                           'This includes, but is not limited to, names, phone numbers, email addresses, physical addresses, social security numbers, and any other personally identifiable information (PII).'
                           'Ensure that the redaction is consistent throughout the text.'
                           'An evaluation agent will review your work and provide you with feedback or tips on how to improve. Understand their feedback and make the necessary changes to your redacted text.'
                           'You must output the redacted text only and not address or respond to any agents directly.',
            llm_config=self.config_list,
            human_input_mode='NEVER',
            code_execution_config=False
        )

        # Define the Evaluation Agent
        self.evaluation = autogen.ConversableAgent(
            'evaluation-agent',
            system_message='You are an evaluation agent tasked with reviewing text to ensure that all personal information has been correctly redacted.'
                           'Your job is to verify that any personal information (such as names, phone numbers, email addresses, physical addresses, social security numbers, and other personally identifiable information) has been replaced with stars (**).'
                           'If you find any personal information that has not been redacted or if the redaction is inconsistent, you should flag the specific issues and provide feedback.'
                           'Ensure that the redaction is thorough and meets the required standards.',
            llm_config=self.config_list,
            human_input_mode='NEVER',
            code_execution_config=False
        )

        # Define the UserProxy Agent
        self.user_proxy = autogen.UserProxyAgent(
            'user_proxy',
            human_input_mode='NEVER',
            code_execution_config=False
        )

        # Define the chat outline
        self.chat_outline = {
            'message': '',
        }

    def text_redact_selection_func(self, speaker: autogen.AssistantAgent, groupchat: autogen.GroupChat):
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

    def redact_text(self, text):
        global conversation_state
        global speakers

        conversation_state = 1
        speakers = []

        # Update chat outline with user-provided text
        self.chat_outline['message'] = text

        # Define the GroupChat and GroupChatManager
        text_redaction_chat = autogen.GroupChat(
            agents=[self.user_proxy, self.text_assistant, self.evaluation],
            speaker_selection_method=self.text_redact_selection_func,
            messages=[],
            max_round=4
        )

        text_redaction_manager = autogen.GroupChatManager(
            groupchat=text_redaction_chat, llm_config=self.config_list
        )

        # Initiate the chat
        text_redaction_chats = self.user_proxy.initiate_chat(
            text_redaction_manager,
            message=self.chat_outline['message']
        )

        # Return the result from the chat
        return text_redaction_chats
