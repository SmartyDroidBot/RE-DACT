from django.shortcuts import render

# Create your views here.


def index(request):
    if request.method == 'POST':
         form_data = {
            'files': request.FILES.getlist('files'),
            'rangeInput': request.POST.get('rangeInput'),
            'wordsTextarea': request.POST.get('wordsTextarea'),
        }
         print("Form Data Received:")
         print(form_data)
    return render(request, 'index.html')
