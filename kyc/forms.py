from django import forms
from .models import KYCApplication, KYCDocument


class KYCApplicationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        required=False
    )

    class Meta:
        model = KYCApplication
        fields = [
            'full_name', 'date_of_birth', 'nationality',
            'address_line1', 'address_line2', 'city', 'country', 'postal_code'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'full_name': 'Full Legal Name',
            'nationality': 'e.g. Filipino',
            'address_line1': 'Street Address',
            'address_line2': 'Apartment, Suite, etc. (optional)',
            'city': 'City',
            'country': 'Country',
            'postal_code': 'Postal Code',
        }
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-input'
            if field_name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[field_name]


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = KYCDocument
        fields = ['document_type', 'file', 'document_number', 'issuing_country', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-input')
        self.fields['file'].widget.attrs.update({
            'class': 'file-input',
            'accept': '.pdf,.jpg,.jpeg,.png',
        })

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Max 10MB
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 10MB.')
            allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                raise forms.ValidationError('Only JPEG, PNG, and PDF files are allowed.')
        return file


class ReviewForm(forms.ModelForm):
    class Meta:
        model = KYCApplication
        fields = ['reviewer_notes', 'risk_level', 'rejection_reason']
        widgets = {
            'reviewer_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-input'}),
            'rejection_reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'risk_level': forms.Select(attrs={'class': 'form-input'}),
        }
