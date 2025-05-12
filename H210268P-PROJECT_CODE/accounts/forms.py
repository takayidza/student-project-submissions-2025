from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import About, CustomUser
from django import forms
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add form-control class to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class CustomResidentCreationForm(UserCreationForm):
    
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add form-control class to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class CustomUserUpdateForm(UserChangeForm):
    password1 = forms.CharField(
        label="New Password", 
        widget=forms.PasswordInput(attrs={"class": "form-control"}), 
        required=False
    )
    password2 = forms.CharField(
        label="Confirm New Password", 
        widget=forms.PasswordInput(attrs={"class": "form-control"}), 
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap styling to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

    def clean_username(self):
        username = self.cleaned_data.get("username")
        user_id = self.instance.id  # Get the user being updated

        # Allow the same username if it's the current user's
        if CustomUser.objects.exclude(id=user_id).filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")

        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # If new passwords are set, update the user's password
        password1 = self.cleaned_data.get("password1")
        if password1:
            user.set_password(password1)

        if commit:
            user.save()
        return user



class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        exclude = ["created_at", "user"]

    def __init__(self, *args, **kwargs):
        super(AboutForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"