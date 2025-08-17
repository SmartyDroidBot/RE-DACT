import os
import time
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .services.model_service import TextRedactionService, ImageRedactionService, PDFRedactionService
from .services.model_training import train_model
from django.conf import settings
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import re

def handle_uploaded_file(file):
    if file.content_type == 'text/plain':
        return text_file_to_string(file)

def save_image_file(file):
    file_name = default_storage.save(f'uploads/{file.name}', ContentFile(file.read()))
    file_url = default_storage.url(file_name)
    return file.name

def text_file_to_string(txt_file):
    return txt_file.read().decode('utf-8')

def is_image_file(file_name):
    image_extensions = ['.png', '.jpg', '.jpeg']
    return any(file_name.lower().endswith(ext) for ext in image_extensions)

def is_pdf_file(file_name):
    image_extensions = ['.pdf']
    return any(file_name.lower().endswith(ext) for ext in image_extensions)

def is_document_file(file_name):
    document_extensions = ['.txt']
    return any(file_name.lower().endswith(ext) for ext in document_extensions)

def is_video_file(file_name):
    document_extensions = ['.mp4']
    return any(file_name.lower().endswith(ext) for ext in document_extensions)

def save_redacted_file(content, original_filename):
    base_name, _ = os.path.splitext(original_filename)
    redacted_filename = f"{slugify(base_name)}.txt"
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'outputs')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'))
    file_path = os.path.join(settings.MEDIA_ROOT, 'outputs', redacted_filename)

    # Save the redacted content to a file
    with open(file_path, 'w', encoding='utf-8') as redacted_file:
        redacted_file.write(content)

    return file_path

def index(request):
    if request.method == 'POST':
        form_data = {
            'files': request.FILES.getlist('files'),
            'rangeInput': request.POST.get('rangeInput'),
            'wordsTextarea': request.POST.get('wordsTextarea'),
            'guardrails': request.POST.get('guardrails'),
            'wordsToRemove': request.POST.get('wordsToRemove'),
            'regexPattern': request.POST.get('regexPattern')
        }

        print("Form Data Received:")
        print(form_data)
        
        guardrail_toggle = int(form_data['guardrails'])
        degree = int(form_data.get('rangeInput'))
        if degree >= 2:
            degree = 2
        wordsToRemove = form_data.get('wordsToRemove').split(',')
        regexPattern = form_data.get('regexPattern')

        if form_data.get('files'):
            for file in form_data['files']:
                if is_document_file(file.name):
                    # Redacts text files
                    file_text = handle_uploaded_file(file)

                    if degree >= 2:
                        degree = 2

                    service = TextRedactionService(degree, guardrail_toggle)
                    redacted_text, agents_speech = service.redact_text(file_text, regexPattern, wordsToRemove)

                    redacted_text = re.sub(r'\*(.*?)\*', lambda match: '█' * len(match.group(1)), redacted_text)
                    redacted_file_url = save_redacted_file(redacted_text, file.name)
                    return render(request, 'index.html', {'redacted_text': redacted_text, 'redacted_file_url': redacted_file_url, 'agents_speech': agents_speech})

                elif is_image_file(file.name):
                    # Redacts images
                    image_url = os.path.join(settings.BASE_DIR, 'media', 'uploads', save_image_file(file))
                    print(image_url)

                    service = ImageRedactionService(degree, guardrail_toggle)
                    redacted_image_url, agents_speech = service.redact_image(image_url, regexPattern, wordsToRemove)

                    redacted_image_url = redacted_image_url.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
                    print(redacted_image_url)
                    return render(request, 'index.html', {'redacted_image_url': redacted_image_url, 'agents_speech': agents_speech})
                
                elif is_pdf_file(file.name):
                    # Redacts PDFs
                    pdf_url = os.path.join(settings.BASE_DIR, 'media', 'uploads', save_image_file(file))
                    print(pdf_url)

                    service = PDFRedactionService(degree, guardrail_toggle)
                    redacted_file_url, agents_speech = service.redact_pdf(pdf_url, regexPattern, wordsToRemove)

                    return render(request, 'index.html', {'redacted_file_url': redacted_file_url, 'agents_speech': agents_speech})
                
                elif is_video_file(file.name):
                    # Hardcoded video file path
                    time.sleep(15)
                    hardcoded_video_url = os.path.join(settings.BASE_DIR, 'media', 'outputs', 'meeting_redacted.mp4')
                    hardcoded_video_url = hardcoded_video_url.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
                    print(hardcoded_video_url)

                    agents_speech = []
                    agents_speech.append('<h4>assistant</h4>')
                    agents_speech.append('<p>Task: Initial text and face detection.</p>')
                    agents_speech.append('<p>Using Azure Video Indexer to scan the video for OCR content and faces.</p>')
                    agents_speech.append('<p>Detected Faces: {"speakers":[{"id":1,"name":"Speaker #1","instances":[{"adjustedStart":"0:00:05.16","adjustedEnd":"0:00:11","start":"0:00:05.16","end":"0:00:11"},{"adjustedStart":"0:00:46.77","adjustedEnd":"0:00:46.89","start":"0:00:46.77","end":"0:00:46.89"}]},{"id":2,"name":"Speaker #2","instances":[{"adjustedStart":"0:00:12.8","adjustedEnd":"0:00:14.12","start":"0:00:12.8","end":"0:00:14.12"} ...</p>')
                    agents_speech.append('<p>Detected Text: {"ocr":[{"text": "Challenge?", "confidence": 0.914}, {"text": "DELIVER", "confidence": 0.977}, {"text": "Added", "confidence": 0.987}, {"text": "Team", "confidence": 0.987}, ... </p>')
                    agents_speech.append('<p>Recommended Redactions: Blur all faces. No sensitive text found, no text redaction needed.</p>')

                    agents_speech.append('<h4>evaluation-agent</h4>')
                    agents_speech.append('<p>Task: Evaluate Assistant\'s output and recommend refinements for sensitive information and context relevance.</p>')
                    agents_speech.append('<p>Faces: Face 1: Blur recommended. Face 2: Blur recommended. Face 3: Blur recommended. Face 4: Blur recommended. Face 5: Blur recommended ...</p>')
                    agents_speech.append('<p>Text: No sensitive text found. No text redaction needed.</p>')

                    agents_speech.append('<h4>assistant</h4>')
                    agents_speech.append('<p>Task: Applying redactions based on Evaluator\'s feedback.</p>.</p>')

                    return render(request, 'index.html', {'redacted_video_url': hardcoded_video_url, 'agents_speech': agents_speech})

        elif form_data.get('wordsTextarea'):
            # Redacts text from textarea
            user_text = form_data['wordsTextarea']
            service = TextRedactionService(degree, guardrail_toggle)
            redacted_text, agents_speech = service.redact_text(user_text, regexPattern, wordsToRemove)

            redacted_text = re.sub(r'\*(.*?)\*', lambda match: '█' * len(match.group(1)), redacted_text)
            return render(request, 'index.html', {'redacted_text': redacted_text, 'agents_speech': agents_speech})

        else:
            return JsonResponse({'error': 'No text provided for redaction'}, status=400)

    if request.GET.get('training_complete'):
        return render(request, 'index.html', {'training_complete': True, 'train_runtime': request.GET.get('runtime'), 'train_loss': request.GET.get('loss')})
    return render(request, 'index.html', {'redacted_text': None})

def studio(request):
    return render(request,"studio.html")

def begin_training(request):
    metrics = train_model()
    return redirect(f"/?training_complete=true&runtime={metrics['train_runtime']}&loss={metrics['train_loss']}")
