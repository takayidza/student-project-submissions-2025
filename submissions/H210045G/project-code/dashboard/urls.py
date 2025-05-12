from django.urls import path
from dashboard.views import DashboardListView

urlpatterns = [
    path('dashboard', DashboardListView.as_view(), name="dashboard"),   
]
