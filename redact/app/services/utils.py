import os
import regex as re
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from django.conf import settings
from PIL import Image, ImageDraw
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

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

    return output_path

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

    return output_path
