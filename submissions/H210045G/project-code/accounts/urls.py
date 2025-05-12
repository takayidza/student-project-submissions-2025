from django.urls import path
from . import views
from accounts.views import CustomPasswordResetView, UserListView, UserUpdateView, UserDeleteView, login_user
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [

    path('users-index', UserListView.as_view(), name="users-index"),
    path('register-user', views.register_user, name="register-user"),
    path('update-user/<int:pk>/', UserUpdateView.as_view(), name="update-user"),
    path('delete-user/<int:pk>/', UserDeleteView.as_view(), name="delete-user"),
    path('', login_user, name="login-user"),


    # user authentication
    # path('', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset.html'), name='password_reset_request'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'), name='password_reset_complete'),
    path('reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('logout-user/', views.logout_user, name="logout-user"),
    path('language/<int:pk>/', views.UserLanguageView.as_view(), name="user-language"),
]
