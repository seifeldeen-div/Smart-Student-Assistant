from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core.validators import FileExtensionValidator

from .models import Profile


class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES[:2])
    cv_file = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])],
    )

    class Meta:
        model = User
        fields = ["username", "email", "role", "cv_file"]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("role") == "instructor":
            if not cleaned_data.get("cv_file"):
                self.add_error("cv_file", "Instructor accounts require a CV.")
        return cleaned_data
