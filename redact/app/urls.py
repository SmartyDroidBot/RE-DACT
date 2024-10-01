from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name="index"),
    path('training/', views.begin_training, name="begin_training")
]