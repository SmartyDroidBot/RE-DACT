import os
from django.shortcuts import render
from django.http import JsonResponse
from .services.model_service import TextRedactionService, ImageRedactionService
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def handle_uploaded_file(file):
    if file.content_type == 'text/plain':
        # Convert text file to string
        return text_file_to_string(file)
    else:
        return None

def save_image_file(file):
    file_name = default_storage.save(f'uploads/{file.name}', ContentFile(file.read()))
    file_url = default_storage.url(file_name)
    return file_url

def text_file_to_string(txt_file):
    return txt_file.read().decode('utf-8')

def is_image_file(file_name):
    image_extensions = ['.png', '.jpg', '.jpeg']
    return any(file_name.lower().endswith(ext) for ext in image_extensions)

def is_document_file(file_name):
    document_extensions = ['.txt', '.doc', '.docx', '.pdf']
    return any(file_name.lower().endswith(ext) for ext in document_extensions)

def save_redacted_file(content, original_filename):
    # Generate a redacted filename (same format as the original file)
    base_name, _ = os.path.splitext(original_filename)
    # Generate a redacted filename with the .txt extension
    redacted_filename = f"{slugify(base_name)}.txt"
    file_path = os.path.join(settings.MEDIA_ROOT, redacted_filename)

    # Save the redacted content to a file
    with open(file_path, 'w', encoding='utf-8') as redacted_file:
        redacted_file.write(content)

    return redacted_filename

def index(request):
    if request.method == 'POST':
        form_data = {
            'files': request.FILES.getlist('files'),
            'rangeInput': request.POST.get('rangeInput'),
            'wordsTextarea': request.POST.get('wordsTextarea'),
        }

        print("Form Data Received:")
        print(form_data)
        degree = int(form_data.get('rangeInput'))
        # Initialize the TextRedactionService
        content = ''
        redacted_text = ''
        # Check if there's text to process
        if form_data.get('files'):
            for file in form_data['files']:
                if is_document_file(file.name):
                    file_text = handle_uploaded_file(file)
                    if file_text:
                        content += file_text
                
                elif is_image_file(file.name):
                    image_url = os.path.join(os.getcwd() + save_image_file(file))
                    print(image_url)

                    service = ImageRedactionService(degree)
                    redacted_image_url = service.redact_image(image_url)

                    return render(request, 'index.html', {'redacted_file_url': redacted_image_url})

        elif form_data.get('wordsTextarea'):
            user_text = form_data['wordsTextarea']
            # Call the redact_text method with the user_text
            service = TextRedactionService(degree)
            redacted_text = service.redact_text(user_text)
            return render(request, 'index.html', {'redacted_text': redacted_text})
        else:
            return JsonResponse({'error': 'No text provided for redaction'}, status=400)



    return render(request, 'index.html', {'redacted_text': None})
