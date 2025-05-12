from django.urls import path
from . import views

urlpatterns = [
    #path('wateronline/', views.dashboard, name='dashboard'),
    path("waterlevel-reports/", views.Reports, name="reports"),
]