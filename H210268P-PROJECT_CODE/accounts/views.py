from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.views import View
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import (
    TemplateView,
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from accounts.models import CustomUser
from .forms import CustomResidentCreationForm, CustomUserCreationForm, CustomUserUpdateForm
from django.contrib.auth.views import PasswordResetView
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth import login
from .models import About
from .forms import AboutForm

class AnonymousUserTemplateView(TemplateView):
    template_name = 'registration/anonymous_user.html' 
    

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
            return redirect('login')
    else:
        return render(request, 'registration/login.html', {})

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
        
class RegisterResidentUserView(View):
    template_name = "registration/user_signup.html"
    form_class = CustomResidentCreationForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = "Resident"  # Assign user_type as "Resident"
            user.save()
            # Log the user in after successful registration
            login(request, user)
            messages.success(request, "Account registered and logged in successfully")
            return redirect('dashboard')
        else:
            # Show actual form errors
            print(form.errors)
            return render(request, self.template_name, {"form": form, "errors": form.errors})


#about page 
class AboutListView(LoginRequiredMixin, ListView):
    model = About
    context_object_name = "abouts"
    template_name = "about/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['first_about'] = About.objects.first()
        return context

class AboutCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = About
    form_class = AboutForm
    template_name = "about/create.html"
    success_message = "About section created successfully"

    def form_valid(self, form):
        form.instance.user = self.request.user  # Associate the About instance with the logged-in user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("about_list")

class AboutUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = About
    form_class = AboutForm
    template_name = "about/update.html"
    success_message = "About section updated successfully"

    def get_success_url(self):
        return reverse("about_list")

class AboutDeleteView(LoginRequiredMixin, SuccessMessageMixin, View):
    def get(self, request, **kwargs):
        obj = get_object_or_404(About, pk=kwargs.get("pk"))
        obj.delete()
        messages.success(request, f"{obj} deleted successfully")
        return HttpResponseRedirect(reverse("about_list"))

class AboutDetailView(LoginRequiredMixin, DetailView):
    model = About
    context_object_name = "about"
    template_name = "about/detail.html"