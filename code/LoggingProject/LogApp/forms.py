from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Users

class createUserForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            ('', 'Role'),               # placeholder
            ('professor', 'Professor'),
            ('TA', 'TA'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:outline-none transition',
        })
    )

    class Meta:
        model = Users
        # Use Django’s built-in password1/password2 fields
        fields = ['first_name', 'last_name', 'email', 'role', 'password1', 'password2']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'First Name',
                'class':       'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:outline-none transition'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Last Name',
                'class':       'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:outline-none transition'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email',
                'class':       'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:outline-none transition'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields
        pw_base = {
            'class':       'w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:outline-none transition',
            'placeholder': 'Password'
        }
        self.fields['password1'].widget.attrs.update(pw_base)

        pw2 = pw_base.copy()
        pw2['placeholder'] = 'Confirm Password'
        self.fields['password2'].widget.attrs.update(pw2)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-emerald-600'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-emerald-600'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-emerald-600'
            }),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500'
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500'
        })
    )