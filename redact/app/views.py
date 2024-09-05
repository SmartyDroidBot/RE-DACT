from django.shortcuts import render
from django.http import JsonResponse
from .services.model_service import TextRedactionService

def index(request):
    if request.method == 'POST':
        form_data = {
            'files': request.FILES.getlist('files'),
            'rangeInput': request.POST.get('rangeInput'),
            'wordsTextarea': request.POST.get('wordsTextarea'),
        }

        print("Form Data Received:")
        print(form_data)

        # Initialize the TextRedactionService
        service = TextRedactionService()

        # Check if there's text to process
        if form_data.get('wordsTextarea'):
            user_text = form_data['wordsTextarea']

            # Call the redact_text method with the user_text
            redacted_text = service.redact_text(user_text)

            # Return the redacted text as a JSON response
            return JsonResponse({'redacted_text': redacted_text})
        else:
            return JsonResponse({'error': 'No text provided for redaction'}, status=400)

    return render(request, 'index.html')
