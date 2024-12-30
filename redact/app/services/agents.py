import os, shutil, urllib
from django.conf import settings
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from ultralytics import YOLO
from django.conf import settings

# Set up models locally
if not os.path.exists(settings.MODEL_PATH):
    os.makedirs('models')
    tokenizer = AutoTokenizer.from_pretrained("lakshyakh93/deberta_finetuned_pii")
    tokenizer.save_pretrained(settings.MODEL_PATH)
    model = AutoModelForTokenClassification.from_pretrained("lakshyakh93/deberta_finetuned_pii")
    model.save_pretrained(settings.MODEL_PATH)

if not os.path.exists(settings.YOLO_MODEL_PATH):
    os.makedirs('yolo')
    download_path = 'https://drive.google.com/file/d/1ZD_CEsbo3p3_dd8eAtRfRxHDV44M0djK/view'
    urllib.request.urlretrieve(download_path, settings.YOLO_MODEL_PATH)

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
        self.assistant = pipeline("token-classification", tokenizer=settings.MODEL_PATH, model=settings.MODEL_PATH , device=-1)
        self.yolo_model = YOLO(settings.YOLO_MODEL_PATH)

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

class AudioRedactionAgents:
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

