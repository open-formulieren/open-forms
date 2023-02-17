from django import forms

from .models import UserPreferences


class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ("ui_language",)
