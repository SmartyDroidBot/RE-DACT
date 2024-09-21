import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from django.conf import settings
from PIL import Image, ImageDraw
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

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


# Load the tokenizer and model from the local directory
model_path = "D:\\Projects\\SIH\\RE-DACT\\redact\\app\\services\\deberta_finetuned_pii" # Fix this path thingy according to your conveniece
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForTokenClassification.from_pretrained(model_path)

# Create the pipeline with your local model
gen = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="first")

def tag_model_output(model_output):
    """
    Returns:
    list: A list of dictionaries with an additional 'tag' key indicating the level.
    """
    level_1 = {
        "SSN", "CREDITCARDNUMBER", "CREDITCARDCVV", "PASSWORD", "IP", "MAC",
        "BITCOINADDRESS", "ETHEREUMADDRESS", "LITECOINADDRESS", "ACCOUNTNUMBER",
        "IBAN", "BIC"
    }
    
    level_2 = {
        "FIRSTNAME", "LASTNAME", "FULLNAME", "NAME", "EMAIL", "PHONE_NUMBER",
        "STREETADDRESS", "CITY", "ZIPCODE", "STATE", "COUNTRY", "JOBTITLE",
        "COMPANY_NAME", "USERNAME"
    }
    
    level_3 = {
        "PREFIX", "MIDDLENAME", "SUFFIX", "JOBDESCRIPTOR", "JOBAREA",
        "SECONDARYADDRESS", "COUNTY", "CURRENCY", "CURRENCYSYMBOL",
        "CURRENCYCODE", "USERAGENT", "SEX", "GENDER", "NEARBYGPSCOORDINATE",
        "DISPLAYNAME", "SEXTYPE", "ORDINALDIRECTION"
    }
    
    def tag_word(word):
        if word in level_1:
            return 1
        elif word in level_2:
            return 2
        elif word in level_3:
            return 3
        else:
            return 999  # Default to level 9 for all other items not classified

    for entity in model_output:
        entity['tag'] = tag_word(entity['entity_group'])
    
    return model_output

def classify_and_tag_text(input_text):
    # Returns a dictionary with words as keys and their corresponding tags as values.
    classified_entities = gen(input_text)
    tagged_entities = tag_model_output(classified_entities)
    word_tag_dict = {entity['word'].strip(): entity['tag'] for entity in tagged_entities}
    return word_tag_dict

def redact_text(input_text, level):
    # Idk how the multi word entries works, its all chatgpt.
    
    # Classify and tag the text
    word_tag_mapping = classify_and_tag_text(input_text)
    
    # Initialize variables
    words = input_text.split()
    redacted_words = []
    i = 0
    
    # Iterate through the words
    while i < len(words):
        word = words[i]
        # Check for multi-word entities
        for entity, tag in word_tag_mapping.items():
            entity_words = entity.split()
            if words[i:i+len(entity_words)] == entity_words:
                if tag <= level:
                    redacted_words.append('■■■■■' * len(entity_words))
                else:
                    redacted_words.extend(entity_words)
                i += len(entity_words) - 1
                break
        else:
            # If no multi-word entity is found, process the single word
            if word_tag_mapping.get(word.strip(), 4) <= level:
                redacted_words.append('■■■■■')
            else:
                redacted_words.append(word)
        i += 1
    
    # Join the redacted words back into a single string
    redacted_text = ' '.join(redacted_words)
    
    return redacted_text
