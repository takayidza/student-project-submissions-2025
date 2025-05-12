from django.urls import path
from . import views

urlpatterns = [
    #path('wateronline/', views.dashboard, name='dashboard'),
    path("send-data/", views.send_data, name="send_data"),
    path("get-latest-water-level/", views.get_latest_water_level, name="get-latest-water-level"),
    path("hourly_water_level", views.Get_Hourly_Data, name="hourly_water_level"),
    path("last24_water_usage/", views.Get_last24_Water_Usage, name="last24_water_usage"),
    path("wateronline/", views.dashboard, name="dashboard"),
]