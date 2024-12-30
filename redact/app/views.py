import os
import time
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.text import slugify
from .services.model_service import TextRedactionService, ImageRedactionService, PDFRedactionService, AudioRedactionService, VideoRedactionService
from .services.model_training import train_model
from django.conf import settings
import re

def handle_uploaded_file(file):
    if file.content_type == 'text/plain':
        return text_file_to_string(file)

def save_image_file(file):
    file_path = f'uploads/{file.name}'
    if default_storage.exists(file_path):
        default_storage.delete(file_path)
    file_name = default_storage.save(file_path, ContentFile(file.read()))
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

def is_audio_file(file_name):
    document_extensions = ['.wav', '.mp3']
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

                    # Check for content safety flag
                    if redacted_text == 'flag':
                        return render(request, 'index.html', {'flag': 'The data you submitted was flagged for content safety violations.'})

                    redacted_text = re.sub(r'\*(.*?)\*', lambda match: '█' * len(match.group(1)), redacted_text)
                    redacted_file_url = save_redacted_file(redacted_text, file.name)
                    return render(request, 'index.html', {'redacted_text': redacted_text, 'redacted_file_url': redacted_file_url, 'agents_speech': agents_speech})

                elif is_image_file(file.name):
                    # Redacts images
                    image_url = os.path.join(settings.BASE_DIR, 'media', 'uploads', save_image_file(file))
                    print(image_url)

                    service = ImageRedactionService(degree, guardrail_toggle)
                    redacted_image_url, agents_speech = service.redact_image(image_url, regexPattern, wordsToRemove)

                    # Check for content safety flag
                    if redacted_image_url == 'flag':
                        return render(request, 'index.html', {'flag': 'The data you submitted was flagged for content safety violations.'})

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
                
                elif is_audio_file(file.name):
                    # Redacts audio
                    audio_url = os.path.join(settings.BASE_DIR, 'media', 'uploads', save_image_file(file))
                    print(audio_url)

                    service = AudioRedactionService(degree, guardrail_toggle)
                    redacted_audio_url, agents_speech = service.redact_audio(audio_url)

                    return render(request, 'index.html', {'redacted_audio_url': redacted_audio_url, 'agents_speech': agents_speech})
                
                elif is_video_file(file.name):
                    # Redacts videos
                    video_url = os.path.join(settings.BASE_DIR, 'media', 'uploads', save_image_file(file))
                    print(video_url)

                    service = VideoRedactionService(degree, guardrail_toggle)
                    redacted_video_url, agents_speech = service.redact_video(video_url)

                    # Check for flags
                    if redacted_video_url == 'error':
                        return render(request, 'index.html', {'error': 'Could not process the video at this time. Please try again later.'})
                    print(redacted_video_url)

                    return render(request, 'index.html', {'redacted_video_url': redacted_video_url, 'agents_speech': agents_speech})
                
        elif form_data.get('wordsTextarea'):
            # Redacts text from textarea
            user_text = form_data['wordsTextarea']
            service = TextRedactionService(degree, guardrail_toggle)
            redacted_text, agents_speech = service.redact_text(user_text, regexPattern, wordsToRemove)

            # Check for content safety flag
            if redacted_text == 'flag':
                return render(request, 'index.html', {'flag': 'The data you submitted was flagged for content safety violations.'})

            redacted_text = re.sub(r'\*(.*?)\*', lambda match: '█' * len(match.group(1)), redacted_text)
            return render(request, 'index.html', {'redacted_text': redacted_text, 'agents_speech': agents_speech})

        else:
            return JsonResponse({'error': 'No text provided for redaction'}, status=400)

    if request.GET.get('training_complete'):
        return render(request, 'index.html', {'training_complete': True, 'train_runtime': request.GET.get('runtime'), 'train_loss': request.GET.get('loss')})
    return render(request, 'index.html', {'redacted_text': None})

def begin_training(request):
    metrics = train_model()
    return redirect(f"/?training_complete=true&runtime={metrics['train_runtime']}&loss={metrics['train_loss']}")
