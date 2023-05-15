from django import forms
from .models import StatFile


class FileForm(forms.ModelForm):
    class Meta:
        model = StatFile
        fields = ["Statement"]
