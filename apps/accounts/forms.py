from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Permission

from .models import Role

User = get_user_model()


class StyledMixin:
    def _style(self):
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            w.attrs.setdefault("class", "input")

    def _decorate(self, meta):
        """meta = {field: (icon, placeholder, autocomplete)} — used by auth templates."""
        for name, (icon, placeholder, autocomplete) in meta.items():
            if name not in self.fields:
                continue
            f = self.fields[name]
            f.icon = icon
            f.widget.attrs.update({"placeholder": placeholder, "autocomplete": autocomplete})
            if self.errors.get(name):
                f.widget.attrs["class"] = f.widget.attrs.get("class", "input") + " is-invalid"
                f.widget.attrs["aria-invalid"] = "true"


class LoginForm(StyledMixin, AuthenticationForm):
    username = forms.CharField(label="Username or email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self._decorate({
            "username": ("user", "you@example.com or username", "username"),
            "password": ("shield", "Your password", "current-password"),
        })


class RegisterForm(StyledMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm password"
        self._decorate({
            "first_name": ("user", "John", "given-name"),
            "last_name": ("user", "Doe", "family-name"),
            "username": ("tag", "johndoe", "username"),
            "email": ("mail", "you@company.com", "email"),
            "password1": ("shield", "At least 8 characters", "new-password"),
            "password2": ("shield", "Repeat your password", "new-password"),
        })

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "company", "avatar", "bio")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class UserAdminForm(StyledMixin, forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput, required=False,
        help_text="Leave blank to keep the current password.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "role", "is_active", "phone", "company")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["password"].required = True
            self.fields["password"].help_text = ""
        self._style()

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user


class RoleForm(StyledMixin, forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related("content_type").filter(
            content_type__app_label__in=["accounts", "core", "blog"]
        ).order_by("content_type__app_label", "content_type__model", "codename"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Role
        fields = ("name", "description", "is_default", "grants_all", "permissions")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()

    def grouped_permissions(self):
        """[(group_label, [(perm, checked), ...]), ...] for the template."""
        selected = {int(x) for x in (self["permissions"].value() or [])}
        groups = {}
        for perm in self.fields["permissions"].queryset:
            ct = perm.content_type
            label = f"{ct.app_label.title()} · {ct.model_class()._meta.verbose_name_plural.title() if ct.model_class() else ct.model}"
            groups.setdefault(label, []).append((perm, perm.pk in selected))
        return groups.items()
