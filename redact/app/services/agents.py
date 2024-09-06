import autogen
from django.conf import settings

config_list = {
    'model': 'llama3.1',
    'base_url': getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434/v1'),
    'api_key': getattr(settings, 'OLLAMA_API_KEY', 'ollama'),
}

class TextRedactionAgents:
    def __init__(self, degree=0):
        text_assistant_prompts = {
            # Degree 0
            0: 'OBJECTIVE: You are an agent designed to redact personal information from any text provided to you.\n' 
            'Your task is to identify and encapsulate any personal information with stars (*).\n'
            'IMPORTANT: This includes this list [Names, Phone numbers, Email addresses, Physical addresses, Social security numbers].'
            'An evaluation agent will review your work and provide you with feedback or tips on how to improve. Understand their feedback and make the necessary changes to your redacted text.'
            'OUTPUT: You must output the original text only with redactions and not address or respond to any agents directly.',

            # Degree 1
            1: 'OBJECTIVE: You are an agent designed to redact personal information from any text provided to you.\n' 
            'Your task is to identify and encapsulate any personal information with stars (*).\n'
            'IMPORTANT: This includes this LIST: [Names, Company Names, Full Dates, Phone numbers, Email addresses, Physical addresses, Social security numbers].'
            'An evaluation agent will review your work and provide you with feedback or tips on how to improve. Understand their feedback and make the necessary changes to your redacted text.'
            'OUTPUT: You must output the orignal text only with redactions and not address or respond to any agents directly.'
        }

        evaluation_prompts = {
            # Degree 0
            0: 'OBJECTIVE: You are an evaluation agent tasked with reviewing text to ensure that all personal information has been correctly redacted.'
            'Your job is to verify that only personal information in this LIST: [Names, Phone numbers, Email addresses, Physical addresses, Social security numbers] has been encapsulated with stars (*).'
            'If you find any personal information in the LIST that has not been redacted or if the redaction is inconsistent, you should flag the specific issues and provide feedback.'
            'OUTPUT: Your output must be in points, stating the additional word(s) to be redacted.',

            # Degree 1
            1: 'OBJECTIVE: You are an evaluation agent tasked with reviewing text to ensure that all personal information has been correctly redacted.'
            'Your job is to verify that any personal information in this LIST: [Names, Company Names, All Proper Nouns, Full Dates, Months, Phone numbers, Email addresses, Physical addresses, Country names, Social security numbers] has been encapsulated with stars (*).'
            'If you find any personal information in the LIST that has not been redacted, you should flag the specific issues and provide feedback.'
            'OUTPUT: Your output must be in points, stating the additional word(s) to be redacted.'
        }

        self.text_assistant = autogen.ConversableAgent(
            'assistant', 
            system_message=text_assistant_prompts[degree],
            llm_config=config_list, 
            human_input_mode='NEVER',
            code_execution_config=False
        )

        self.evaluation = autogen.ConversableAgent(
            'evaluation-agent',
            system_message=evaluation_prompts[degree],
            llm_config=config_list,
            human_input_mode='NEVER',
            code_execution_config=False
        )


class ImageRedactionAgents:
    def __init__(self, degree=0):
        image_assistant_prompts = {
            # Degree 0
            0: 'OBJECTIVE: You are an agent designed to identify personal information from any text provided to you.\n'
            'Your sole task is to output a Python list of words or phrases that need to be redacted based on the following categories:'
            '[Names, Proper Nouns, Company Names, Full Dates, Phone Numbers, Email Addresses, Physical Addresses, Social Security Numbers].\n'
            'IMPORTANT: Your output MUST strictly be a SINGLE Python list of strings representing the items that need to be redacted.'
            'Example Output: ["John Doe", "123-456-7890"].\n'
            'You should NOT respond with explanations, code blocks, or any other format.\n'
            'DO NOT explain or comment on your reasoning; just output the list.\n'
            'FAILURE EXAMPLE (do not output this): "The following need to be redacted..."\n'
            'SUCCESS EXAMPLE (the correct output): ["John Doe", "123-456-7890"].'
        }

        evaluation_prompts = {
            0: 'OBJECTIVE: You are an evaluation agent responsible for reviewing text to ensure that all personal information has been correctly redacted.\n'
                'Your task is to verify whether any personal information from the following LIST has been missed: '
                '[Names, Proper Nouns, Company Names, Full Dates, Months, Phone Numbers, Email Addresses, Physical Addresses, Country Names, Social Security Numbers].\n'
                'If any of this information is still present, flag the specific issue and provide feedback on the missing redactions.\n'
                'IMPORTANT: You must list the exact words or phrases that still need to be redacted without modifying them in any way.\n'
                'INPUT: List of words or phrases that need to be redacted.\n'
                'Example Input: ["John Doe", "123-456-7890"].\n'
                'OUTPUT: Provide your feedback as bullet points, listing any additional word(s) or phrases that need to be redacted.\n'
                'Example Output:\n'
                '- "John Doe" (Name)\n'
                '- "123-456-7890" (Phone Number)\n'
                'You MUST NOT change the words or phrases. DO NOT redact or censor them with asterisks or any other symbols. Just list them in their original form.'
        }

        self.image_assistant = autogen.ConversableAgent(
            'assistant', 
            system_message=image_assistant_prompts[degree],
            llm_config=config_list, 
            human_input_mode='NEVER',
            code_execution_config=False
        )

        self.evaluation = autogen.ConversableAgent(
            'evaluation-agent',
            system_message=evaluation_prompts[degree],
            llm_config=config_list,
            human_input_mode='NEVER',
            code_execution_config=False
        )


user_proxy = autogen.UserProxyAgent(
    'user_proxy', 
    human_input_mode='NEVER',
    code_execution_config=False
)
