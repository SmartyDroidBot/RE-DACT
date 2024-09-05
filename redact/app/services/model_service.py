import autogen
from .agents import config_list
from .agents import TextRedactionAgents, user_proxy

class TextRedactionService:
    def __init__(self, degree):
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
