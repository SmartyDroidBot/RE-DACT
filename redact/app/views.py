import os
from django.shortcuts import render
from django.http import JsonResponse
from .services.model_service import TextRedactionService
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils.text import slugify

def handle_uploaded_file(file):
    if file.content_type == 'text/plain':
        # Convert text file to string
        return text_file_to_string(file)
    else:
        return None

def text_file_to_string(txt_file):
    return txt_file.read().decode('utf-8')

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
        service = TextRedactionService(degree)
        text_content = ''
        redacted_text = ''
        # Check if there's text to process
        if form_data.get('files'):
            for file in form_data['files']:
                file_text = handle_uploaded_file(file)
                if file_text:
                    text_content += file_text
            redacted_text = service.redact_text(text_content)
            original_filename = file.name

            # Save the redacted content to a new file
            redacted_filename = save_redacted_file(redacted_text, original_filename)
            redacted_file_url = default_storage.url(redacted_filename)

            return render(request, 'index.html', {'redacted_file_url': redacted_file_url,'redacted_text':redacted_text})

        elif form_data.get('wordsTextarea'):
            user_text = form_data['wordsTextarea']
            # Call the redact_text method with the user_text
            redacted_text = service.redact_text(user_text)
            return render(request, 'index.html', {'redacted_text': redacted_text})
        else:
            return JsonResponse({'error': 'No text provided for redaction'}, status=400)



    return render(request, 'index.html', {'redacted_text': None})
