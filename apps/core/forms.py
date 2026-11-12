from django import forms

from .models import ContactMessage, ServiceRequest


class ContactForm(forms.ModelForm):
    BUDGETS = [
        ("<500", "Under $500"), ("500-2k", "$500 – 2k"), ("2k-5k", "$2k – 5k"),
        ("5k+", "$5k+"), ("unsure", "Not sure yet"),
    ]
    website = forms.CharField(required=False, widget=forms.HiddenInput)  # honeypot
    budget = forms.ChoiceField(choices=BUDGETS, required=False, widget=forms.RadioSelect)

    # field -> (icon, placeholder, autocomplete)
    META = {
        "name": ("user", "Your full name", "name"),
        "email": ("mail", "you@company.com", "email"),
        "phone": ("phone", "+880 1XXX-XXXXXX", "tel"),
        "subject": ("tag", "e.g. New SaaS platform", "off"),
        "message": ("pen", "Tell me about your project — goals, features, timeline…", "off"),
    }

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "budget", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 6, "maxlength": 2000})}
        labels = {"name": "Full name", "email": "Email address", "phone": "Phone / WhatsApp"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, (icon, placeholder, autocomplete) in self.META.items():
            f = self.fields[name]
            f.icon = icon
            cls = "input is-invalid" if self.is_bound and self.errors.get(name) else "input"
            f.widget.attrs.update({"class": cls, "placeholder": placeholder, "autocomplete": autocomplete})

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ("service", "title", "description", "budget", "deadline")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "input")
