from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, ProfileForm, RegisterForm


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    extra_context = {"auth_mode": "login"}

    def get_context_data(self, **kwargs):
        # Django's LoginView injects its own "site"/"site_name" (the Sites framework),
        # which would shadow our SiteSetting from the context processor.
        ctx = super().get_context_data(**kwargs)
        ctx.pop("site", None)
        ctx.pop("site_name", None)
        return ctx


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()  # default role assigned automatically by signal
        login(request, user, backend="apps.accounts.backends.RoleBackend")
        messages.success(request, "Welcome aboard! Your account is ready.")
        return redirect("dashboard:home")
    return render(request, "accounts/register.html", {"form": form, "auth_mode": "register"})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "dashboard/profile.html", {"form": form, "section": "profile"})


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "dashboard/password_change.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Password changed successfully.")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for f in form.fields.values():
            f.widget.attrs["class"] = "input"
        return form
