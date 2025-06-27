from django import forms
from .models import Admin
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import make_password
from .models import Voter
from .models import Poll, Candidate


class AdminSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Admin
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        admin = super().save(commit=False)
        admin.password = make_password(self.cleaned_data['password'])  # Hashing
        if commit:
            admin.save()
        return admin
class AdminLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['name', 'description', 'start_date', 'end_date', 'poll_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['poll_type'].widget.attrs.update({'class': 'form-check-input'})
class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'image', 'description']
class VoterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Voter
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        voter = super().save(commit=False)
        voter.password = make_password(self.cleaned_data['password'])  # Hash it
        if commit:
            voter.save()
        return voter
class PollEditForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['name', 'description', 'end_date', 'poll_type']
        widgets = {
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
class PasswordVerificationForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
class CandidateEditForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
class PollDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="I confirm I want to delete this poll and all its data"
    )
    password = forms.CharField(widget=forms.PasswordInput)