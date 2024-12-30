# REDACT: Responsible AI FAQs

## What is REDACT?

REDACT is an application that allows for universal redaction across multiple file types. It does so using an agent based on a [custom fine-tuned DeBERTa LLM](https://huggingface.co/lakshyakh93/deberta_finetuned_pii) on token classification, which detects Personally Identifiable Information (PII) in text. The agent is supported via multiple Azure services that allow for the redaction of PDFs, images, and audio. An additional YOLO model detects faces in images and can redact them, while videos are redacted via Azure Video Indexer.

## What can REDACT do?

REDACT can automate requirements and workflows in domains that necessitate redaction, such as in legal, healthcare, and financial sectors.

Example use cases in various domains:

- **Legal**: Redaction is required in court proceedings and other legal documents to comply with privacy laws. For example, Social Security numbers, financial account numbers, and home addresses are commonly redacted in court filings.
- **Healthcare**: Redaction is used to protect patient confidentiality by removing sensitive data like medical details and patient identifiers from healthcare records.
- **Finance**: Redaction removes sensitive information from financial records, employee reports, compliance documents, and other filings.

## What is/are REDACT's intended use(s)?

Please note the REDACT is an open-source application under active development and intended for use for research purposes. It should not be used in any downstream applications without additional detailed evaluation of robustness, safety issues, and assessment of any potential harm or bias in the proposed application.

REDACT's example uses include:

- **Data Privacy Compliance**: Redact sensitive information in legal documents, contracts, and agreements.
- **Legal Discovery & Document Review**: Streamlines the redaction of privileged or confidential information in documents during litigation or discovery processes.
- **Medical Research**: Anonymizes data in clinical studies and research reports for public sharing while safeguarding patient privacy.
- **Educational Content**: Redacts sensitive or identifiable data in assignments, exam scripts, and presentations.
- **Financial Documents**: Redacts account numbers, credit card details, and other sensitive financial information from invoices, statements, and reports.
- **Data anonymization in AI/ML**: Redacts sensitive information in training datasets to create compliant, anonymized datasets for AI/ML development.

## What are the limitations of REDACT?

REDACT relies on multiple existing frameworks and is subject to the common limitations of its dependencies:

- **Data Biases**: The data used to train the agent may carry biases. The agent may not classify PII correctly, due to its potentially biased or unfair training process.
- **OCR Limitations**: Optical Character Recognition (OCR) is the process of extracting text from images. REDACT is subject to the limitations of Azure Document Intelligence Read API, which implements OCR, such as poor performance on handwritten documents.
- **Speech-to-Text Limitations**: REDACT is subject to the limitations of Azure Speech Service, that may not be able to process audio accurately.
- **Video Redaction Limitations**: REDACT is subject to the limitations of Azure Video Indexer, which implements redaction for faces detected in videos. For example, the service may not be able to detect faces accurately.
- **Content Harms**: REDACT is subject to the limitations of Azure Content Safety, which enforces content safety for all inputs excluding videos.
- **Offline Capabilities**: REDACT can run offline for text-based redaction. However, for PDF and image redaction that require OCR, the application can run offline through [Azure AI containers](https://learn.microsoft.com/en-us/azure/ai-services/cognitive-services-container-support). To the best of our knowledge, Azure Video Indexer does not support offline usage.
