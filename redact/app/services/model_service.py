import os
import re
import time
from .agents import TextRedactionAgents, ImageRedactionAgents, PDFRedactionAgents, AudioRedactionAgents
from .guardrails import guardrail_azure_cs_text, guardrail_azure_cs_image, guardrail_proper_nouns, guardrail_numbers, guardrail_urls, guardrail_emails
from .db_service import uploadOutputDB
from .utils import azure_image_ocr, azure_pdf_ocr, azure_speech_to_text, azure_upload_video, match_regexPattern, export_redacted_image, export_redacted_pdf, export_redacted_audio
from azure.identity import DefaultAzureCredential
from django.conf import settings

class TextRedactionService:
    """
        The service for redacting text and text files.

        __init___ inputs:
            degree: Degree of redaction, as selected by client.
            guardrail_toggle: Whether guardrails should be turned on or not, default is 1.
        __init__ output:
            A TextRedactionService object.

        redact_text inputs:
            text: Entered by the client.
            regexPattern: Custom regex pattern, if entered by the client.
            wordsToRemove: Custom words to redact, if entered by the client.
        redact_text outputs:
            redacted_text: Final redacted text.
            agents_speech: Steps carried by agents and guardrails, to establish a logical flow for the client.

    """

    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = guardrail_toggle

        self.assistant = TextRedactionAgents(degree).assistant
        self.degree0_list = TextRedactionAgents(degree).degree0_list
        self.degree1_list = TextRedactionAgents(degree).degree1_list
        self.degree2_list = TextRedactionAgents(degree).degree2_list

    def redact_text(self, text, regexPattern, wordsToRemove=[]):
        word_list = text.split()
        redacted_list = []
        redacted_list_from_agent = [] + [j for i in wordsToRemove for j in i.split()]
        output_db_list = [] # Storing outputs for improving models

        content_safety_flag = guardrail_azure_cs_text(word_list)
        if content_safety_flag:
            return 'flag', []

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
                'label': 'B-' + entity['entity_group'] # Adding B- prefix to entity_group
            })
            output_db_list.append({
                'word': entity['word'],
                'label': 'I-' + entity['entity_group'] # Adding I- prefix to entity_group
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
    '''
        The service for redacting text and faces in images.

        __init___ inputs:
            degree: Degree of redaction, as selected by client.
            guardrail_toggle: Whether guardrails should be turned on or not, default is 1.
        __init__ output:
            An ImageRedactionService object.

        redact_image inputs:
            image: Inputted by the client.
            regexPattern: Custom regex pattern, if entered by the client.
            wordsToRemove: Custom words to redact, if entered by the client.
        redact_image outputs:
            output_path: Path to the redacted image.
            agents_speech: Steps carried by agents and guardrails, to establish a logical flow for the client.

    '''
    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = 0
        # Temporary: Toggling guardrails on for 3rd degree only
        if degree == 2 and guardrail_toggle:
            self.guardrail_toggle = 1

        self.assistant = ImageRedactionAgents(degree).assistant
        self.yolo_model = ImageRedactionAgents(degree).yolo_model
        self.degree0_list = ImageRedactionAgents(degree).degree0_list
        self.degree1_list = ImageRedactionAgents(degree).degree1_list
        self.degree2_list = ImageRedactionAgents(degree).degree2_list
    
    def redact_image(self, image, regexPattern, wordsToRemove=[]):
        result = azure_image_ocr(image)
        word_list = result.content.split()
        redacted_list = []
        output_db_list = [] # Storing outputs for improving models

        content_safety_flag = guardrail_azure_cs_image(image)
        if content_safety_flag:
            return 'flag', []

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
                'label': 'B-' + entity['entity_group'] # Adding B- prefix to entity_group
            })
            output_db_list.append({
                'word': entity['word'],
                'label': 'I-' + entity['entity_group'] # Adding I- prefix to entity_group
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
            redacted_list, agents_speech = self.guardrails(redacted_list_from_agent, word_list, agents_speech)
        else:
            redacted_list = redacted_list_from_agent
        redacted_list = sorted(redacted_list, key=len, reverse=True)

        # Extract redacted words and their coordinates
        redacted_cords = self.extract_redacted_words_coordinates(redacted_list, result)

        # Extract faces
        redacted_cords = redacted_cords + self.extract_faces(image)

        # Export redacted image
        output_path = export_redacted_image(image, redacted_cords)

        return output_path, agents_speech
    
    # Extract faces
    def extract_faces(self, image):
        redacted_cords = []
        results = self.yolo_model(image, classes=[0])
        for result in results:
            if len(result.boxes.xyxy) > 0:
                for i in range(len(result.boxes.xyxy)):
                    redacted_cords.append(result.boxes.xyxy[i].tolist())
        
        return redacted_cords
    
    # Guardrails are called only for last degree
    def guardrails(self, redacted_list_from_agent, word_list, agents_speech):
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

        return redacted_list, agents_speech
    
    # Extract redacted words and their coordinates
    def extract_redacted_words_coordinates(self, redacted_list, result):
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
        
        return redacted_cords
    
    
class PDFRedactionService:
    """
        The service for redacting PDF files.

        __init___ inputs:
            degree: Degree of redaction, as selected by client.
            guardrail_toggle: Whether guardrails should be turned on or not, default is 1.
        __init__ output:
            A PDFRedactionService object.

        redact_pdf inputs:
            pdf: Entered by the client.
            regexPattern: Custom regex pattern, if entered by the client.
            wordsToRemove: Custom words to redact, if entered by the client.
        redact_text outputs:
            output_path: Path to the redacted pdf.
            agents_speech: Steps carried by agents and guardrails, to establish a logical flow for the client.

    """

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
        output_db_list = [] # Stores outputs for improving models
        redacted_list_from_agent = [] + [j for i in wordsToRemove for j in i.split()]

        content_safety_flag = guardrail_azure_cs_text(word_list)
        if content_safety_flag:
            return 'flag', []

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
                'label': 'B-' + entity['entity_group'] # Adding B- prefix to entity_group
                })
                output_db_list.append({
                    'word': entity['word'],
                    'label': 'I-' + entity['entity_group'] # Adding I- prefix to entity_group
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
            redacted_list, agents_speech = self.guardrails(redacted_list_from_agent, word_list, agents_speech)
        else:
            redacted_list = redacted_list_from_agent
        redacted_list = sorted(redacted_list, key=len, reverse=True)

        # Extract redacted words and their coordinates
        redacted_cords, page_dims = self.extract_redacted_words_coordinates(redacted_list, result)

        # Export redacted PDF
        output_path = export_redacted_pdf(pdf, redacted_cords, page_dims)

        return output_path, agents_speech
    
    # Guardrails are called only for last degree
    def guardrails(self, redacted_list_from_agent, word_list, agents_speech):
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

        return redacted_list, agents_speech
    
    # Extract redacted words and their coordinates
    def extract_redacted_words_coordinates(self, redacted_list, result):
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
        
        return redacted_cords, page_dims


class AudioRedactionService:
    """
        The service for redacting audio files.

        __init___ inputs:
            degree: Degree of redaction, as selected by client.
            guardrail_toggle: Whether guardrails should be turned on or not, default is 1.
        __init__ output:
            An AudioRedactionService object.

        redact_audio inputs:
            audio: Entered by the client.
            wordsToRemove: Custom words to redact, if entered by the client. Has no functionality yet.
        redact_audio outputs:
            output_path: Path to the redacted audio file.
            agents_speech: Steps carried by agents and guardrails, to establish a logical flow for the client.

    """

    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = guardrail_toggle

        self.assistant = AudioRedactionAgents(degree).assistant
        self.degree0_list = AudioRedactionAgents(degree).degree0_list
        self.degree1_list = AudioRedactionAgents(degree).degree1_list
        self.degree2_list = AudioRedactionAgents(degree).degree2_list

    def redact_audio(self, audio, wordsToRemove=[]):    
        result, transcription_json = azure_speech_to_text(audio) # Transcription json contains the transcript along with timestamps
        word_list = result.split()
        redacted_list = []
        redacted_list_from_agent = []
        output_db_list = [] # Stores outputs for improving models

        content_safety_flag = guardrail_azure_cs_text(word_list)
        if content_safety_flag:
            return 'flag', []
        
        raw_redacted_list_from_agent = self.assistant(result, aggregation_strategy="first")
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
                'label': 'B-' + entity['entity_group'] # Adding B- prefix to entity_group
            })
            output_db_list.append({
                'word': entity['word'],
                'label': 'I-' + entity['entity_group'] # Adding I- prefix to entity_group
            })
        
        redacted_list_from_agent = list(set(redacted_list_from_agent))
        uploadOutputDB(output_db_list)

        # Return chat history
        agents_speech = []
        agents_speech.append('<h4>' + 'assistant' + '</h4>')
        agents_speech.append('<p>Redacting words: ' + str(redacted_list_from_agent) + '</p>')

        # Guardrails are called only for last degree
        if self.guardrail_toggle:
            redacted_list, agents_speech = self.guardrails(redacted_list_from_agent, word_list, agents_speech)
        else:
            redacted_list = redacted_list_from_agent
        redacted_list = sorted(redacted_list, key=len, reverse=True)

        # Extract redacted words and their timestamps
        redacted_timestamps = self.extract_redacted_words_timestamps(redacted_list, transcription_json)

        # Export redacted audio
        output_path = export_redacted_audio(audio, redacted_timestamps)
        
        return output_path, agents_speech
    
    # Guardrails are called only for last degree
    def guardrails(self, redacted_list_from_agent, word_list, agents_speech):
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

        return redacted_list, agents_speech
    
    # Extract redacted words and their timestamps
    def extract_redacted_words_timestamps(self, redacted_list, transcription_json):
        redacted_timestamps = []
        for phrase in transcription_json['phrases']:
            for word in phrase['words']:
                for redacted_word in redacted_list:
                    if redacted_word in word['text'] or redacted_word.strip() in word['text'].strip():
                        redacted_timestamps.append((word['offsetMilliseconds'], word['offsetMilliseconds'] + word['durationMilliseconds']))
        
        return redacted_timestamps
    

class VideoRedactionService:
    '''
        The service for redacting faces in videos using Azure Video Indexer (VI).

        __init___ inputs:
            degree: Degree of redaction, as selected by client. Has no functionality yet.
            guardrail_toggle: Whether guardrails should be turned on or not, default is 1. Has no functionality yet.
        __init__ output:
            A VideoRedactionService object.

        redact_video inputs:
            video: Inputted by the client.
        redact_video outputs:
            output_path: URL to the redacted video in VI.
            agents_speech: Steps carried by agents and guardrails, to establish a logical flow for the client. Has no functionality yet.

    '''
    def __init__(self, degree=0, guardrail_toggle=1):
        self.degree = degree
        self.guardrail_toggle = guardrail_toggle

    def redact_video(self, video):
        import requests

        video_name = os.path.basename(video)
        video_url = azure_upload_video(video)

        # Get VI token
        vi_default_credential = DefaultAzureCredential()
        vi_scope = f'{settings.AZURE_VI_RESOURCE_MANAGER}/.default'
        vi_token = vi_default_credential.get_token(vi_scope).token

        # Get VI access token
        headers = {
            'Authorization': 'Bearer ' + vi_token,
            'Content-Type': 'application/json'
        }
        params = {
            'permissionType': 'Contributor',
            'scope': 'Account'
        }
        vi_access_token_request = requests.post(
            url=f'{settings.AZURE_VI_RESOURCE_MANAGER}/subscriptions/{settings.AZURE_VI_SUBSCRIPTION}/resourceGroups/{settings.AZURE_VI_RESOURCE_GROUP}/providers/Microsoft.VideoIndexer/accounts/{settings.AZURE_VI_NAME}/generateAccessToken?api-version=2024-01-01',
            json=params,
            headers=headers
        )
        vi_access_token = vi_access_token_request.json().get('accessToken')

        # TEMPORARY: Delete all videos in VI
        vi_get_videos_request = requests.get(
            f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos?accessToken={vi_access_token}'
        )
        for video in vi_get_videos_request.json().get('results'):
            vi_video_delete_request = requests.delete(
                url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{video.get("id")}?accessToken={vi_access_token}'
            )            

        # Upload the video to VI
        vi_video_upload_request = requests.post(
            url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos?name={video_name}&videoUrl={video_url}&privacy=public&accessToken={vi_access_token}',
            json=params
        )

        vi_video_id = None
        if vi_video_upload_request.status_code == 200:
            vi_video_id = vi_video_upload_request.json().get('id')
        else: # If video already exists
            match = re.search(r"video id: '(\w+)'", vi_video_upload_request.json().get('Message'))
            if match:
                vi_video_id = match.group(1)
            else:
                return 'error', []

        # Poll to check indexing
        vi_video_poll_request = requests.get(
            url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{vi_video_id}/Index?accessToken={vi_access_token}',
            json=params
        )

        polling_count = 0
        while (vi_video_poll_request.json().get('state') != "Processed" and polling_count < 60):
            time.sleep(10)
            vi_video_poll_request = requests.get(
                url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{vi_video_id}/Index?accessToken={vi_access_token}',
                json=params
            )
            polling_count += 1
            if vi_video_poll_request.json().get('state') == "Failed":
                return 'error', []
        if vi_video_poll_request.json().get('state') != "Processed":
            return 'error', []

        # Redact the video (redacts faces)
        vi_redacted_video = video_name.replace('.mp4', '_redacted.mp4')
        params = {
            "faces": {
                "blurringKind": "LowBlur"
            }
        }
        vi_video_redact_request = requests.post(
            url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{vi_video_id}/redact?name={vi_redacted_video}&accessToken={vi_access_token}',
            json=params
        )
        
        # Find the id for the redacted video
        vi_get_videos_request = requests.get(
            f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos?accessToken={vi_access_token}'
        )
        vi_video_redacted_id = None
        for video in vi_get_videos_request.json().get('results'):
            if video.get('name') == vi_redacted_video:
                vi_video_redacted_id = video.get('id')
                break

        # Get an access token for the redacted video
        headers = {
            'Authorization': 'Bearer ' + vi_token,
            'Content-Type': 'application/json'
        }

        params = {
            'permissionType': 'Contributor',
            'scope': 'Video',
            'videoId': vi_video_redacted_id
        }

        vi_video_redacted_access_token_request = requests.post(
            url=f'{settings.AZURE_VI_RESOURCE_MANAGER}/subscriptions/{settings.AZURE_VI_SUBSCRIPTION}/resourceGroups/{settings.AZURE_VI_RESOURCE_GROUP}/providers/Microsoft.VideoIndexer/accounts/{settings.AZURE_VI_NAME}/generateAccessToken?api-version=2024-01-01',
            json=params,
            headers=headers
        )
        vi_video_redacted_access_token = vi_video_redacted_access_token_request.json().get('accessToken')

        # Poll for redacted video indexing
        vi_video_redacted_poll_request = requests.get(
            url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{vi_video_redacted_id}/Index?accessToken={vi_video_redacted_access_token}',
            json=params
        )

        polling_count = 0
        while (vi_video_redacted_poll_request.json().get('state') != "Processed" and polling_count < 60):
            time.sleep(10)
            vi_video_redacted_poll_request = requests.get(
                url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{vi_video_redacted_id}/Index?accessToken={vi_video_redacted_access_token}',
                json=params
            )
            polling_count += 1
            if vi_video_redacted_poll_request.json().get('state') == "Failed":
                return 'error', []
        if vi_video_redacted_poll_request.json().get('state') != "Processed":
            return 'error', []

        # Get a URL for the redacted video
        from urllib.parse import quote
        vi_video_redacted_download_request = requests.get(
            f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{vi_video_redacted_id}/SourceFile/DownloadUrl?accessToken={vi_video_redacted_access_token}'
        )        
        vi_video_redacted_url = vi_video_redacted_download_request.json().replace(vi_redacted_video, quote(vi_redacted_video))

        # Delete original video from VI when done
        vi_video_delete_request = requests.delete(
            url=f'https://api.videoindexer.ai/{settings.AZURE_VI_LOCATION}/Accounts/{settings.AZURE_VI_ID}/Videos/{vi_video_id}?accessToken={vi_access_token}'
        )

        return vi_video_redacted_url, []
            
