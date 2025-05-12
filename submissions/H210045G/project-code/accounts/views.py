from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from accounts.models import CustomUser
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from django.contrib.auth.views import PasswordResetView
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, (f"You have successfully logged in as: {user.username}"))
            return redirect('dashboard')       
        else:
            messages.success(request, ("Please check your credentials and try again"))
            return redirect('login-user')
    else:
        return render(request, 'account/login.html', {})

class UserListView(ListView):
    model = CustomUser
    template_name = 'registration/index.html'

def register_user(request):
        if request.method == "GET":
            return render(
                request, "registration/create.html",
                {"form": CustomUserCreationForm}
            )
        elif request.method == "POST":
            form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, ("User created successfully"))
            return redirect('users-index')
        else:
            messages.success(request, ("Something went wrong please try again"))
            return redirect('register-user')
        

class UserUpdateView(UpdateView):
    model = CustomUser
    template_name = 'registration/update.html'
    form_class = CustomUserUpdateForm
    success_message = "User updated successfully"   
    def get_success_url(self):
        return reverse("users-index")

class UserDeleteView(LoginRequiredMixin, View):
    def get(self, request, **kwargs):
        obj = get_object_or_404(CustomUser, pk=kwargs.get("pk"))
        obj.delete()
        messages.success(request, "User deleted successfully")
        return HttpResponseRedirect(reverse("users-index"))

#Custom email reset 

class CustomPasswordResetView(PasswordResetView):
    email_template_name = 'account/password_reset_email.html'
    html_email_template_name = 'account/password_reset_email.html'

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        html_email = render_to_string(html_email_template_name, context)
        email_message = EmailMessage(
            subject_template_name,
            html_email,
            from_email,
            [to_email],
        )

        email_message.content_subtype = 'html'
        email_message.send()
        

def logout_user(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('login-user')

class UserLanguageView(LoginRequiredMixin, View):

    def post(self, request, **kwargs):
        obj = get_object_or_404(CustomUser, pk=kwargs.get("pk"))

        if request.POST:
            language = request.POST.get('language')
            obj.language = language
            obj.save()
            messages.success(request, "Language updated successfully")
            return redirect(request.META.get("HTTP_REFERER", "/")) 
        else:
            messages.error(request, 'You didn\'t provide a language')

        return render(request, 'update_language.html', {'obj': obj})