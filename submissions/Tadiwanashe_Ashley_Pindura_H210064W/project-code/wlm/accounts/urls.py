from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    #path('login/', views.login, name='login'),
]