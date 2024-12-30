import datetime
import os
import regex as re
import requests
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.ai.formrecognizer import DocumentAnalysisClient
from django.conf import settings
from PIL import Image, ImageDraw
from pydub import AudioSegment
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO, StringIO

# Azure OCR function for images
def azure_image_ocr(image):
    endpoint = settings.AZURE_DI_ENDPOINT
    key = settings.AZURE_DI_KEY

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    
    with open(image, "rb") as form_file:
        poller = document_analysis_client.begin_analyze_document(
            model_id="prebuilt-read", document=form_file
        )
        result = poller.result()
    
    return result

# Azure OCR function for PDFs
def azure_pdf_ocr(pdf):
    endpoint = settings.AZURE_DI_ENDPOINT
    key = settings.AZURE_DI_KEY

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    
    with open(pdf, "rb") as form_file:
        poller = document_analysis_client.begin_analyze_document(
            model_id="prebuilt-read", document=form_file
        )
        result = poller.result()
    
    return result

# Azure speech-to-text function
def azure_speech_to_text(audio_path):
    key = settings.AZURE_SI_KEY
    endpoint = settings.AZURE_SI_ENDPOINT

    audio = open(audio_path, "rb").read()

    headers = {
        "Ocp-Apim-Subscription-Key": key
    }
    files = {
        "audio": audio
    }
    fast_transcription_request = requests.post(f"{endpoint}/speechtotext/transcriptions:transcribe?api-version=2024-11-15", headers=headers, files=files)
    
    text = ''
    if fast_transcription_request.status_code == 200:
        text = fast_transcription_request.json()['combinedPhrases'][0]['text']

    return text, fast_transcription_request.json()

# Azure function to upload video to storage account
def azure_upload_video(video_path):
    video_name = os.path.basename(video_path)
    storage_credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=settings.AZURE_STORAGE_URL, credential=storage_credential)
    container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
    user_delegation_key = blob_service_client.get_user_delegation_key(
        key_start_time=datetime.datetime.now(datetime.timezone.utc),
        key_expiry_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    )

    with open(file=video_path, mode="rb") as video_file:
        video_blob = container_client.upload_blob(name=video_name, data=video_file, overwrite=True)
    
    video_url = f'{settings.AZURE_STORAGE_URL}/{settings.AZURE_STORAGE_CONTAINER}/{video_name}'

    return video_url

# Function to extract Regex matches from text
def match_regexPattern(text, regexPattern):
    matches = re.findall(regexPattern, text)
    return matches

# Export redacted image
def export_redacted_image(image_path, redacted_cords):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # For each set of coordinates, draw the black boxes
    for coord_set in redacted_cords:
        try: # For words
            x_coords = [point[0] for point in coord_set]
            y_coords = [point[1] for point in coord_set]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
        
        except: # For faces
            x_min, y_min, x_max, y_max = coord_set

        finally:
            draw.rectangle([x_min, y_min, x_max, y_max], fill='black')

    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'outputs')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'))
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', os.path.basename(image_path))
    image.save(output_path)

    relative_output_path = os.path.relpath(output_path, settings.MEDIA_ROOT)
    return os.path.join(settings.MEDIA_URL, relative_output_path)

# Export redacted PDF
def export_redacted_pdf(pdf_path, redacted_cords, page_dims):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # For each set of coordinates, draw black boxes
        if page_num < 2:
            for coord_set in redacted_cords[page_num]:
                x_coords = [point[0] for point in coord_set]
                y_coords = [point[1] for point in coord_set]
                x_min, x_max = min(x_coords) / page_dims[page_num][0] * page_width, max(x_coords) / page_dims[page_num][0] * page_width
                y_min, y_max = page_height - (min(y_coords) / page_dims[page_num][1] * page_height), page_height - (max(y_coords) / page_dims[page_num][1] * page_height)

                can.setFillColorRGB(0, 0, 0)
                can.rect(x_min, y_min, (x_max - x_min), (y_max - y_min), stroke=0, fill=1)

        # Finalize the canvas for the page
        can.save()

        # Merge the redaction onto the page
        packet.seek(0)
        new_pdf = PdfReader(packet)
        if new_pdf.pages:
            page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'outputs')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'))
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', os.path.basename(pdf_path))
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    relative_output_path = os.path.relpath(output_path, settings.MEDIA_ROOT)
    return os.path.join(settings.MEDIA_URL, relative_output_path)

# Export redacted audio
def export_redacted_audio(audio_path, redacted_timestamps):
    audio = AudioSegment.from_file(audio_path)
    
    for start_time, end_time in redacted_timestamps:
        if 0 <= start_time < len(audio) and 0 < end_time <= len(audio):
            # Replace the segment with silence
            silence = AudioSegment.silent(duration=end_time - start_time)
            audio = audio[:start_time] + silence + audio[end_time:]
    
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'outputs')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'))
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', os.path.basename(audio_path))
    audio.export(output_path, format='wav')

    relative_output_path = os.path.relpath(output_path, settings.MEDIA_ROOT)
    return os.path.join(settings.MEDIA_URL, relative_output_path)
