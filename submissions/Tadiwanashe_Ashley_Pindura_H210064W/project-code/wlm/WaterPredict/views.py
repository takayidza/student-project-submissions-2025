from django.shortcuts import render
from Dashboard import models

# Create your views here.
def Predictions(request):
    return render(request, "WaterPredict/Predictions.html")