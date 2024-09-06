from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

endpoint = "https://redact-document.cognitiveservices.azure.com/"
key = ""

def azure_image_ocr(image):
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    
    with open(image, "rb") as form_file:
        poller = document_analysis_client.begin_analyze_document(
            model_id="prebuilt-read", document=form_file
        )
        result = poller.result()
    
    return result
