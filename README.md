# Re-Dact: An AI-powered Universal Redaction Service

## Description

REDACT is a novel application for the automatic, AI-powered, universal redaction of sensitive information across text, PDFs, images, and video file types, complemented by a robust fine-tuning process, guardrails, and content safety mechanisms.

## Key Features

REDACT offers the following key features:

- **Redacting text**: Redact text and `.txt` files, with offline usage supported, across 116 categories of Personally Identifiable Information (PII). Example categories include account & banking information, Personal information like names and contact information.
- **Redacting PDFs**: Runs Optical Character Recognition (OCR) to extract all text, followed by the aforementioned redaction approach. All 116 categories are supported.
- **Redacting Images**: Runs OCR again to extract text, followed by the same redaction approach. All 116 categories are supported. 
- **Redacting Videos**: Runs Azure Video Indexer to upload the submitted video to an Azure service, redacts all faces, and returns a URL for the same. 
- **Varying Degrees of Redaction**: Different degrees of redaction are supported for text, PDFs, and images, based on the user's needs.

## Running the App

- **Azure Service Key Configuration**: Service keys for Azure Document Intelligence, Speech Service, Video Indexer, and Content Safety must be entered in `redact/app/services/service_keys.json`. Document Intelligence, Speech Service, and Content Safety only require an endpoint and a key. Video Indexer requires the name, ID, a subscription ID, and the endpoint. It also requires an Azure Storage Account.
- **Install all requirements in `requirements.txt`**
- **Run the Django app**: Run the application via `python redact/app/manage.py runserver`. 


## Key Files

- **redact/app/services/**: Contains redaction related modules.
  - `agents.py`: Manages the agent, the DeBERTa LLM used in the application.
  - `db_service.py`: Handles database operations for storing classifications, that can be used to fine-tune the agent later.
  - `guardrails.py`: Implements guardrails for redaction services.
  - `model_service.py`: Manages the redaction services and workflows for text, PDFs, images, and videos.
  - `service_keys.json`: Stores service keys for all Azure services.
  - `utils.py`: Contains utility functions used across the application.

- **redact/models/**: Contains the agent's configuration and weights.

- **redact/manage.py/**: Used to run the Django application.

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).
