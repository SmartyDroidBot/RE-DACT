from django.db import models

# Create your models here.
class modelTrainingData(models.Model):
    word = models.CharField(max_length=256,null=False)
    label = models.CharField(max_length=256,null=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Time stamp: {self.timestamp}"

