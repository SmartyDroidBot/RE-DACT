import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from django.conf import settings
from PIL import Image, ImageDraw

# Azure OCR function for images
def azure_image_ocr(image):
    endpoint = settings.AZURE_ENDPOINT
    key = settings.AZURE_KEY

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    
    with open(image, "rb") as form_file:
        poller = document_analysis_client.begin_analyze_document(
            model_id="prebuilt-read", document=form_file
        )
        result = poller.result()
    
    return result

# Export redacted image
def export_redacted_image(image_path, redacted_cords):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # For each set of coordinates, draw the black boxes
    for coord_set in redacted_cords:
        x_coords = [point[0] for point in coord_set]
        y_coords = [point[1] for point in coord_set]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        draw.rectangle([x_min, y_min, x_max, y_max], fill='black')

    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'outputs')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'outputs'))
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', os.path.basename(image_path))
    image.save(output_path)

    return output_path
