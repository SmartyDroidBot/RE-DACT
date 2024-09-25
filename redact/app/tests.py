from django.test import TestCase
from .services.db_service import ModelData
from .models import modelTrainingData
# Create your tests here.
class ModelDataTest(TestCase):

    def test_model_data_insertion(self):
        # Sample data
        dict_struct = [
            {"word":"Shashwat","label":"If you fall for nothing, what do you stand for?"},
            {"word":"Povidone-iodine","label":"I like to get garglled"}
        ]

        # Call the function
        ModelData(dict_struct)

        # Check that the data was added correctly
        self.assertEqual(modelTrainingData.objects.count(), 2)
        self.assertEqual(modelTrainingData.objects.first().word, 'Shashwat')
        self.assertEqual(modelTrainingData.objects.last().label, 'I like to get garglled')