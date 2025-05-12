from django.urls import path
from . import views

urlpatterns = [
    #path('wateronline/', views.dashboard, name='dashboard'),
    path("womp-hourly-water-usage/", views.predict_hourly_water_usage, name="predict"),
    path("waterlevels/", views.monitor_water_levels, name="monitor_waterlevels"),
    path("weeklyusage/", views.predict_weekly_usage, name="weekly_usage"),
    path("weatherforecast/", views.weather_forecast, name="weather_forecast"),
]