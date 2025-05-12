from django.urls import path
from . import views

urlpatterns = [
    #path('wateronline/', views.dashboard, name='dashboard'),
    path("predict-water-level/", views.Predictions, name="predict"),
]