from django.urls import path
from . import views
from accounts.views import AboutCreateView, AboutDeleteView, AboutDetailView, AboutListView, AboutUpdateView, CustomPasswordResetView, RegisterResidentUserView, UserListView, UserUpdateView, UserDeleteView
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [

    path('users-index', UserListView.as_view(), name="users-index"),
    path('register-user', views.register_user, name="register-user"),
    path('update-user/<uuid:id>/', UserUpdateView.as_view(), name="update-user"),
    path('delete-user/<uuid:id>/', UserDeleteView.as_view(), name="delete-user"),
    path('register-resident-user', RegisterResidentUserView.as_view(), name="register-resident-user"),
    path('anonymous-user/', views.AnonymousUserTemplateView.as_view(), name="anonymous-user"),

    # user authentication
    path('', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset.html'), name='password_reset_request'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'), name='password_reset_complete'),
    path('reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    
    #about 
    path('about/', AboutListView.as_view(), name="about_list"),
    path('about/create/', AboutCreateView.as_view(), name="about_create"),
    path('about/update/<uuid:pk>/', AboutUpdateView.as_view(), name="about_update"),
    path('about/delete/<uuid:pk>/', AboutDeleteView.as_view(), name="about_delete"),
    path('about/<uuid:pk>/', AboutDetailView.as_view(), name="about_detail"),
]
