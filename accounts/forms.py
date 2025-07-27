from django import forms
from .models import Admin, Voter, Poll, Candidate
from django.contrib.auth.hashers import make_password


# --- Admin Signup ---
class AdminSignUpForm(forms.ModelForm):
    # Password field: make sure it's masked in the browser
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Admin
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        # Overriding the default save to hash the password before saving
        admin = super().save(commit=False)
        admin.password = make_password(self.cleaned_data['password'])  # 🔐 Hashing the password
        if commit:
            admin.save()
        return admin


# --- Admin Login ---
class AdminLoginForm(forms.Form):
    # Simple form (not model-based), handles admin login credentials
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


# --- Poll Creation ---
class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['name', 'description', 'start_date', 'end_date', 'poll_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'  # lets admin choose date/time from picker
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adds Bootstrap styling to poll_type checkboxes
        self.fields['poll_type'].widget.attrs.update({'class': 'form-check-input'})


# --- Candidate Creation ---
class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'image', 'description']


# --- Voter Creation ---
class VoterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Voter
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        # Hash the password before saving to DB
        voter = super().save(commit=False)
        voter.password = make_password(self.cleaned_data['password'])  # 🔐 Security best practice
        if commit:
            voter.save()
        return voter


# --- Poll Editing ---
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


# --- Password Verification (e.g., before deleting polls) ---
class PasswordVerificationForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)


# --- Candidate Editing ---
class CandidateEditForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# --- Poll Deletion Confirmation Form ---
class PollDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="I confirm I want to delete this poll and all its data"
    )
    password = forms.CharField(widget=forms.PasswordInput)


# --- Voter Validation Form ---
class VoterValidationForm(forms.Form):
    # Input fields: user must enter their name and email
    username = forms.CharField(max_length=150)
    email = forms.EmailField()

    def clean(self):
        """
        Called when form.is_valid() is triggered.

        Purpose:
        - Verifies that a voter exists with the given username/email.
        - Ensures the voter has not already voted.
        - Passes the voter instance into cleaned_data so the view can use it.
        """
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        # Step 1: Check if any voter matches
        if not Voter.objects.filter(username=username, email=email).exists():
            raise forms.ValidationError("Voter not found or invalid credentials.")

        # Step 2: Get the first match (in case duplicates exist in dev/test)
        voter = Voter.objects.filter(username=username, email=email).first()

        # Step 3: Prevent duplicate voting
        if voter.has_voted:
            raise forms.ValidationError("This voter has already voted.")

        # Step 4: Pass this voter object to the view through cleaned_data
        cleaned_data['voter'] = voter
        return cleaned_data
