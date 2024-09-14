import os
from django.shortcuts import render
from django.http import JsonResponse
from .services.model_service import TextRedactionService, ImageRedactionService
from .services.guardrails import guardrail_capitalized_words,guardrail_proper_nouns,guardrail_proper_nouns_list
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

def is_document_file(file_name):
    document_extensions = ['.txt', '.doc', '.docx', '.pdf']
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
            'guardrails': request.POST.get('guardrails') #guardrail value,
        }

        print("Form Data Received:")
        print(form_data)
        print("check if guardrail returned")
        print(form_data['guardrails'])
        degree = int(form_data.get('rangeInput'))
        if degree >= 2:
            degree = 2

        if form_data.get('files'):
            for file in form_data['files']:
                if is_document_file(file.name):
                    # Redacts text files
                    file_text = handle_uploaded_file(file)

                    service = TextRedactionService(degree)
                    redacted_text, agents_speech = service.redact_text(file_text)

                    redacted_text = re.sub(r'\*(.*?)\*', lambda match: '█' * len(match.group(1)), redacted_text)
                    redacted_file_url = save_redacted_file(redacted_text, file.name)
                    return render(request, 'index.html', {'redacted_text': redacted_text, 'redacted_file_url': redacted_file_url, 'agents_speech': agents_speech})

                elif is_image_file(file.name):
                    # Redacts images
                    image_url = os.path.join(settings.BASE_DIR, 'media', 'uploads', save_image_file(file))
                    print(image_url)

                    # Temporary degree check
                    if degree >=1:
                        degree = 1

                    service = ImageRedactionService(degree)
                    redacted_image_url, agents_speech = service.redact_image(image_url)

                    return render(request, 'index.html', {'redacted_file_url': redacted_image_url, 'agents_speech': agents_speech})

        elif form_data.get('wordsTextarea'):
            # Redacts text from textarea
            user_text = form_data['wordsTextarea']
            service = TextRedactionService(degree)
            redacted_text, agents_speech = service.redact_text(user_text)

            redacted_text = re.sub(r'\*(.*?)\*', lambda match: '█' * len(match.group(1)), redacted_text)
            return render(request, 'index.html', {'redacted_text': redacted_text, 'agents_speech': agents_speech})

        else:
            return JsonResponse({'error': 'No text provided for redaction'}, status=400)

    return render(request, 'index.html', {'redacted_text': None})
