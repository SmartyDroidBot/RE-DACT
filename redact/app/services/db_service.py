from ..models import modelTrainingData
import pandas as pd

def uploadOutputDB(dict_struct):
   # To create a new object and push it into the database do the below
   for data in dict_struct:
      modelTrainingData.objects.create(**data)
   # (**) is used to let django know to convert the dictionary key:values to be mapped onto the django model class.

def getDBDataframe():
   response = modelTrainingData.objects.all().values()
   df = pd.DataFrame(response)
   return df

