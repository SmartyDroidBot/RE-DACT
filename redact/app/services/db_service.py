from ..models import modelTrainingData
def ModelData(dict_struct):
    
    #To create a new object and push it into the database do the below
    for data in dict_struct:
       modelTrainingData.objects.create(**data)
    # (**) is used to let django know to convert the dictionary key:values to be mapped onto the django model class.
