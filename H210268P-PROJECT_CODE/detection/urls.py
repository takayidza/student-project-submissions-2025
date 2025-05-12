from django.urls import path

from .views import (
    AccidentAreaHistoryListView,
    AlertListView,
    DestinationTemplateView,
    JourneyDetailView,
    JourneyListView,
    JourneyStartView,
    SettingListView,
    SettingCreateView,
    SettingUpdateView,
    SettingDeleteView,
    SettingDetailView,
    create_alert,
    latest_alert,
    safety_alert,
)

urlpatterns = [
    path('setting/', SettingListView.as_view(), name='setting_list'),
    path('setting/create/', SettingCreateView.as_view(), name='setting_create'),
    path('setting/<uuid:pk>/update/', SettingUpdateView.as_view(), name='setting_update'),
    path('setting/<uuid:pk>/delete/', SettingDeleteView.as_view(), name='setting_delete'),
    path('setting/<uuid:pk>/', SettingDetailView.as_view(), name='setting_detail'),
    
    #accident areas history
    path('accident-areas/history/', AccidentAreaHistoryListView.as_view(), name='accident_area_history_list'),
    
    #destination 
    path('destination/', DestinationTemplateView.as_view(), name='destination_template'),
    path('create_alert/', create_alert, name='create_alert'),

    #alerts
    path('alerts/', AlertListView.as_view(), name='alert_list'),
    path('api/latest-alert/', latest_alert, name='latest_alert'),
    path('api/safety-alert/', safety_alert, name='safety_alert'),

    
    #user journey
    path('journey/', JourneyListView.as_view(), name='journey_list'),
    path('journey/startOrArrive/<uuid:pk>/', JourneyStartView.as_view(), name='journey_start'),
    path('journey/<uuid:pk>/', JourneyDetailView.as_view(), name='journey_detail'),
]