from django.urls import path
from . import views

urlpatterns = [
    #path('wateronline/', views.dashboard, name='dashboard'),
    path("firmware-update/", views.firmware_update, name="firmware_update"),
]