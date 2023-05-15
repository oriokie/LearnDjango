from django import forms
from .models import File
from .models import StatFile


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ["Statement", "Cheques", "EFTs", "Direct_Debit"]


class StatForm(forms.ModelForm):
    class Meta:
        model = StatFile
        fields = ["Statement"]
