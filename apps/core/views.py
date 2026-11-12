from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .forms import ContactForm
from .models import PageContent, Project, Service, Technology


def _can_preview(request):
    return request.user.is_authenticated and request.user.has_perm("core.change_pagecontent")


def render_page(request, page, **extra):
    """Render any page (built-in or custom) from its sections."""
    if not page.is_published and not _can_preview(request):
        raise Http404
    sections = page.sections.filter(is_active=True)
    return render(request, "core/page.html", {"page": page, "sections": sections, **extra})


def home(request):
    return render_page(request, PageContent.get("home"), stats={
        "projects": Project.objects.filter(is_published=True).count(),
        "services": Service.objects.filter(is_active=True).count(),
        "technologies": Technology.objects.count(),
    })


def about(request):
    return render_page(request, PageContent.get("about"))


def services(request):
    return render_page(request, PageContent.get("services"))


def portfolio(request):
    return render_page(request, PageContent.get("portfolio"))


def pricing(request):
    return render_page(request, PageContent.get("pricing"))


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks! Your message has been received. I'll reply within 24 hours.")
            return redirect("core:contact")
        messages.error(request, "Please fix the errors below.")
    return render_page(request, PageContent.get("contact"), contact_form=form)


def custom_page(request, slug):
    page = get_object_or_404(PageContent, page="custom", slug=slug)
    return render_page(request, page)


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    return render(request, "core/service_detail.html", {
        "service": service,
        "others": Service.objects.filter(is_active=True).exclude(pk=service.pk)[:3],
        "projects": Project.objects.filter(is_published=True)[:3],
    })


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, is_published=True)
    return render(request, "core/project_detail.html", {
        "project": project,
        "related": Project.objects.filter(is_published=True, category=project.category)
        .exclude(pk=project.pk)[:3],
    })


def privacy(request):
    return render(request, "core/privacy.html")


@require_GET
def robots_txt(request):
    from django.conf import settings

    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /accounts/",
        "Allow: /",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
