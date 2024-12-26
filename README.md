# REDACT: An AI-powered Universal Redaction Service

## Description

REDACT is a novel application for the automatic, AI-powered, universal redaction of sensitive information across text, PDFs, images, and video file types, complemented by a robust fine-tuning process, guardrails, and content safety mechanisms.

## Key Features

REDACT offers the following key features:

- **Redacting text**: Redact text and `.txt` files, with offline usage supported, across 116 categories of Personally Identifiable Information (PII). Example categories include account & banking information, Personal information like names and contact information.
- **Redacting PDFs**: Runs Optical Character Recognition (OCR) to extract all text, followed by the aforementioned redaction approach. All 116 categories are supported.
- **Redacting Images**: Runs OCR again to extract text, followed by the same redaction approach. All 116 categories are supported. Also runs a computer vision model to detect faces in the image, and redacts them.
- **Redacting Videos**: Runs Azure Video Indexer to upload the submitted video to an Azure service, redacts all faces, and returns a URL for the same. 
- **Fine-tuning the system to your need**: After sufficient redactions, previous classifications can be used to fine-tune the model to suit your needs.
- **An easy-to-use Frontend**: The application's simple and beautiful frontend allows quick access to redaction, as well as other tools to enhance its quality.

## Technical Approach

- **Text**: The agent for all text-based redaction is based on a [custom fine-tuned DeBERTa LLM](https://huggingface.co/lakshyakh93/deberta_finetuned_pii), on token classification for extracting PII.
- **PDFs**: Uses Azure Document Intelligence Read API (OCR), that returns text and bounding boxes. The extracted text is then run through the agent, and redaction marks are drawn on the files.
- **Images**: Similar to PDFs, uses Azure Document Intelligence followed by DeBERTa LLM to redact text. Faces are redacted in images using YOLO (You-Only-Look-Once) v8.
- **Videos**: Uses Azure Video Indexer API to redact faces found in videos.
- **Model Training**:The agent can be further fine-tuned, using previously classified data, that is logged via Django Models.
- **Content Safety**: Implemented through Azure Content Safety that blocks text, PDFs, and images with hate, self-harm, sexual content, and violence.
- **Guardrails**: Includes simple guardrails for always redacting proper nouns (through NLTK), numbers, URLs, and emails. 
- **Process Overview**: The frontend showcases the process overview that achieved the redaction. This portrays the various roles played by the agent and the guardrails.
- **Other enhancements**: The user can enter regex patterns and a custom list of words to be redacted.

## Future Updates

- **Audio Redaction**: Implement via text-to-speech models, followed by redaction through the agent.
- **Content Safety for Videos**
- **Threaded processes for redaction services**
- **API services**

## Frameworks & Cloud Technologies Used

- **HuggingFace**: Runs and trains the DeBERTa LLM for classifying PII.
- **Azure Document Intelligence**: Runs OCR on PDFs and images.
- **Azure Video Indexer**: Redacts faces in videos.
- **Azure Content Safety**: Implements content safety on text, PDFs, and images.
- **Ultralytics**: Runs YOLO, for redacting faces in images.
- **Django**: Backend framework.

## Running the App

- **Azure Service Key Configuration**: Service keys for Azure Document Intelligence, Video Indexer, and Content Safety must be entered in `redact/app/services/service_keys.json`. Document Intelligence and Content Safety only requires an endpoint and a key. Video Indexer requires the name, ID, a subscription ID, and the endpoint. It also requires an Azure Storage Account.
- **Install all requirements in `requirements.txt`**
- **Run the Django app**: Run the application via `python redact/app/manage.py runserver`. 

## Transparency FAQs

Please check `TRANSPARENCY_FAQS.md` for more information on responsible AI use.

## Directory Structure

```shell
├── redact
│   ├── app
│   │    ├── migrations
│   │    │    ├── __init__.py
│   │    │    ├── 0001_initial.py
│   │    │    ├── 0002_rename_classes_modeltrainingdata_label.py
│   │    ├── services
│   │    │    ├── agents.py
│   │    │    ├── db_service.py
│   │    │    ├── guardrails.py
│   │    │    ├── model_service.py
│   │    │    ├── model_training.py
│   │    │    ├── service_keys.json
│   │    │    ├── utils.py
│   │    ├── static
│   │    │    ├── images
│   │    │    │    ├── arrow-up.png
│   │    │    ├── index.css
│   │    ├── templates
│   │    │    ├── index.html
│   │    ├── __init__.py
│   │    ├── admin.py
│   │    ├── apps.py
│   │    ├── models.py
│   │    ├── tests.py
│   │    ├── urls.py
│   │    ├── views.py
│   ├── models
│   │    ├── config.json
│   │    ├── merges.txt
│   │    ├── model.safetensors
│   │    ├── special_tokens_map.json
│   │    ├── tokenizer_config.json
│   │    ├── tokenizer.json
│   │    ├── vocab.json
│   ├── redact
│   │    ├── __init__.py
│   │    ├── asgi.py
│   │    ├── settings.py
│   │    ├── urls.py
│   │    ├── wsgi.py
│   ├── yolo
│   │    ├── yolov8n_100e.pt
│   ├── manage.py
├── .gitattributes
├── .gitignore
├── LICENSE.md
├── README.md
├── TRANSPARENCY_FAQS.md
└── requirements.txt
```

## Main Files and Their Purposes

- **redact/app/services/**: Contains redaction related modules.
  - `agents.py`: Manages the agent, the DeBERTa LLM used in the application.
  - `db_service.py`: Handles database operations for storing classifications, that can be used to fine-tune the agent later.
  - `guardrails.py`: Implements guardrails for redaction services.
  - `model_service.py`: Manages the redaction services and workflows for text, PDFs, images, and videos.
  - `model_training.py`: Handles fine-tuning the model.
  - `service_keys.json`: Stores service keys for all Azure services.
  - `utils.py`: Contains utility functions used across the application.

- **redact/models/**: Contains the agent's configuration and weights.

- **redact/yolo/**: Contains the model weights for YOLO.

- **redact/manage.py/**: Used to run the Django application.

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).
