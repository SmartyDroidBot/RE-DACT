import os
from django.conf import settings
from PIL import Image, ImageDraw
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract' # add path to tesseract.exe

# Load the tokenizer and model from the local directory
model_path = os.path.join(os.path.dirname(__file__), 'deberta_finetuned_pii')
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

def image_redaction(image_path, level):
    """
    Opens an image, extracts text using OCR, classifies and tags the text, and redacts words based on the specified level.

    Args:
        image_path (str): The path to the image file.
        level (int): The classification level threshold for redaction.

    Returns:
        str: The path to the redacted image.
    """
    # Check if the file exists
    if not os.path.isfile(image_path):
        print(f"File {image_path} not found.")
        return None

    # Open the image file
    image = Image.open(image_path)

    # Use pytesseract to do OCR on the image
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    # Extract text and bounding box coordinates
    words = data['text']
    confidences = data['conf']
    x_coords = data['left']
    y_coords = data['top']
    widths = data['width']
    heights = data['height']

    # Filter out words with low confidence
    filtered_words = [
        {
            'word': word,
            'conf': conf,
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        for word, conf, x, y, width, height in zip(words, confidences, x_coords, y_coords, widths, heights)
        if int(conf) > 60  # You can adjust the confidence threshold as needed
    ]

    # Combine the words into a single string for classification
    input_text = ' '.join([word['word'] for word in filtered_words])

    # Classify and tag the text
    word_tag_dict = classify_and_tag_text(input_text)

    # Add classification tags to the filtered words
    for word_info in filtered_words:
        word_info['tag'] = word_tag_dict.get(word_info['word'], 999)  # Default to 999 if not found

    # Make a copy of the image to draw on
    redacted_image = image.copy()
    draw = ImageDraw.Draw(redacted_image)

    # Iterate over the classified words and draw black boxes on words with tag <= level
    for word_info in filtered_words:
        if word_info['tag'] <= level:
            x = word_info['x']
            y = word_info['y']
            width = word_info['width']
            height = word_info['height']
            draw.rectangle([(x, y), (x + width, y + height)], fill="black")

    # Save the redacted image
    output_folder = os.path.join(settings.MEDIA_ROOT, 'outputs')
    os.makedirs(output_folder, exist_ok=True)
    base_name, ext = os.path.splitext(os.path.basename(image_path))
    output_path = os.path.join(output_folder, f'{base_name}_redacted_{level}{ext}')
    redacted_image.save(output_path)
    
    return output_path
