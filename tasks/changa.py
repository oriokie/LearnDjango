from django import forms

class DonationForm(forms.Form):
    name = forms.CharField(max_length=100)
    donation = forms.DecimalField(max_digits=10, decimal_places=2)
