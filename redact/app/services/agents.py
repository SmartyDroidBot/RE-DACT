import os
from django.conf import settings
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from django.conf import settings

config_list = {
    'model': 'llama3.1',
    'base_url': getattr(settings, 'OLLAMA_API_URL', 'http://localhost:11434/v1'),
    'api_key': getattr(settings, 'OLLAMA_API_KEY', 'ollama'),
}

# Set up models locally
if not os.path.exists('models'):
    os.makedirs('models')
    tokenizer = AutoTokenizer.from_pretrained("lakshyakh93/deberta_finetuned_pii")
    tokenizer.save_pretrained(settings.MODEL_PATH)
    model = AutoModelForTokenClassification.from_pretrained("lakshyakh93/deberta_finetuned_pii")
    model.save_pretrained(settings.MODEL_PATH)

class TextRedactionAgents:
    def __init__(self, degree=0):
        self.assistant = pipeline("token-classification", tokenizer=settings.MODEL_PATH, model=settings.MODEL_PATH , device=-1)

        self.degree0_list = [
            "SSN", "PASSWORD", "CREDITCARDNUMBER", "CREDITCARDCVV", "ACCOUNTNUMBER", "IBAN",
            "BITCOINADDRESS", "ETHEREUMADDRESS", "LITECOINADDRESS", "PHONEIMEI", "MAC", 
            "CREDITCARDISSUER", "VEHICLEVIN", "VEHICLEVRM", "ACCOUNTNAME"
        ]

        self.degree1_list = [
            "FIRSTNAME", "LASTNAME", "FULLNAME", "NAME", "JOBTITLE", "COMPANY_NAME", "EMAIL", 
            "PHONE_NUMBER", "USERNAME", "ADDRESS", "IPV4", "IPV6", "STREETADDRESS", "CITY", 
            "STATE", "ZIPCODE", "DATE", "TIME", "URL", "IP"
        ]

        self.degree2_list = [
            "JOBTYPE", "JOBDESCRIPTOR", "JOBAREA", "SEX", "GENDER", "COUNTY", "BUILDINGNUMBER", 
            "SECONDARYADDRESS", "CURRENCY", "AMOUNT", "SEXTYPE", "ORDINALDIRECTION", 
            "DISPLAYNAME", "NUMBER", "NEARBYGPSCOORDINATE", "CURRENCYCODE", "CURRENCYSYMBOL"
        ]


class ImageRedactionAgents:
    def __init__(self, degree=0):
        self.assistant = pipeline("token-classification", "lakshyakh93/deberta_finetuned_pii", device=-1)

        self.degree0_list = [
            "SSN", "PASSWORD", "CREDITCARDNUMBER", "CREDITCARDCVV", "ACCOUNTNUMBER", "IBAN",
            "BITCOINADDRESS", "ETHEREUMADDRESS", "LITECOINADDRESS", "PHONEIMEI", "MAC", 
            "CREDITCARDISSUER", "VEHICLEVIN", "VEHICLEVRM", "ACCOUNTNAME"
        ]

        self.degree1_list = [
            "FIRSTNAME", "LASTNAME", "FULLNAME", "NAME", "JOBTITLE", "COMPANY_NAME", "EMAIL", 
            "PHONE_NUMBER", "USERNAME", "ADDRESS", "IPV4", "IPV6", "STREETADDRESS", "CITY", 
            "STATE", "ZIPCODE", "DATE", "TIME", "URL", "IP"
        ]

        self.degree2_list = [
            "JOBTYPE", "JOBDESCRIPTOR", "JOBAREA", "SEX", "GENDER", "COUNTY", "BUILDINGNUMBER", 
            "SECONDARYADDRESS", "CURRENCY", "AMOUNT", "SEXTYPE", "ORDINALDIRECTION", 
            "DISPLAYNAME", "NUMBER", "NEARBYGPSCOORDINATE", "CURRENCYCODE", "CURRENCYSYMBOL"
        ]

class PDFRedactionAgents:
    def __init__(self, degree=0):
        self.assistant = pipeline("token-classification", "lakshyakh93/deberta_finetuned_pii", device=-1)

        self.degree0_list = [
            "SSN", "PASSWORD", "CREDITCARDNUMBER", "CREDITCARDCVV", "ACCOUNTNUMBER", "IBAN",
            "BITCOINADDRESS", "ETHEREUMADDRESS", "LITECOINADDRESS", "PHONEIMEI", "MAC", 
            "CREDITCARDISSUER", "VEHICLEVIN", "VEHICLEVRM", "ACCOUNTNAME"
        ]

        self.degree1_list = [
            "FIRSTNAME", "LASTNAME", "FULLNAME", "NAME", "JOBTITLE", "COMPANY_NAME", "EMAIL", 
            "PHONE_NUMBER", "USERNAME", "ADDRESS", "IPV4", "IPV6", "STREETADDRESS", "CITY", 
            "STATE", "ZIPCODE", "DATE", "TIME", "URL", "IP"
        ]

        self.degree2_list = [
            "JOBTYPE", "JOBDESCRIPTOR", "JOBAREA", "SEX", "GENDER", "COUNTY", "BUILDINGNUMBER", 
            "SECONDARYADDRESS", "CURRENCY", "AMOUNT", "SEXTYPE", "ORDINALDIRECTION", 
            "DISPLAYNAME", "NUMBER", "NEARBYGPSCOORDINATE", "CURRENCYCODE", "CURRENCYSYMBOL"
        ]

