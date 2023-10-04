from django import forms
from django.contrib.auth.models import User
from store.models import User


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'm_name', 'last_name', 'password']

class EditProfileForm(forms.ModelForm):
    company_name = forms.CharField(max_length=255, required=False)
    company_phone = forms.CharField(max_length=255, required=False)
    company_email_address = forms.CharField(max_length=255, required=False)
    billing_address_line1 = forms.CharField(max_length=255, required=False)
    billing_address_line2 = forms.CharField(max_length=255, required=False)
    billing_city = forms.CharField(max_length=255, required=False)
    billing_state = forms.CharField(max_length=255, required=False)
    billing_zipcode = forms.CharField(max_length=255, required=False)
    billing_country = forms.CharField(max_length=255, required=False)
    shipping_address_line1 = forms.CharField(max_length=255, required=False)
    shipping_address_line2 = forms.CharField(max_length=255, required=False)
    shipping_city = forms.CharField(max_length=255, required=False)
    shipping_state = forms.CharField(max_length=255, required=False)
    shipping_zipcode = forms.CharField(max_length=255, required=False)
    shipping_country = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'username', 'company_name', 'company_phone', 'company_email_address',
            'billing_address_line1', 'billing_address_line2', 'billing_city', 'billing_state', 'billing_zipcode', 'billing_country',
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city', 'shipping_state', 'shipping_zipcode', 'shipping_country'
        ]
