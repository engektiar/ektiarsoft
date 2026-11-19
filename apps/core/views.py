from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

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


def _ocr_remaining(user):
    from django.utils import timezone

    from . import ocr
    from .models import OcrUsage

    used = OcrUsage.objects.filter(user=user, day=timezone.localdate()).values_list("count", flat=True).first() or 0
    return max(0, ocr.daily_limit() - used)


@require_GET
def image_to_text(request):
    """OCR tool. Free mode runs entirely in the visitor's browser (Tesseract.js).
    AI mode (logged-in users) sends the image to Claude; nothing is stored either way."""
    from . import ocr

    ctx = {"ai_enabled": ocr.ai_enabled(), "ai_limit": ocr.daily_limit()}
    if request.user.is_authenticated:
        ctx["ai_remaining"] = _ocr_remaining(request.user)
    return render(request, "core/image_to_text.html", ctx)


@require_POST
def image_to_text_ai(request):
    """AI mode: JSON {"image": "data:image/jpeg;base64,..."} -> {"text": "..."}.
    The image and the text are not stored; only today's usage count is."""
    import base64
    import binascii
    import json

    from django.db import transaction
    from django.db.models import F
    from django.http import JsonResponse
    from django.utils import timezone

    from . import ocr
    from .models import OcrUsage

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Please log in to use AI mode."}, status=401)
    if not ocr.ai_enabled():
        return JsonResponse({"error": "AI mode is not set up yet."}, status=503)
    if _ocr_remaining(request.user) <= 0:
        return JsonResponse({"error": f"Daily AI limit reached ({ocr.daily_limit()}). Try again tomorrow."}, status=429)
    try:
        payload = json.loads(request.body or b"{}")
        header, b64 = payload["image"].split(",", 1)
        media_type = header.split(";")[0].removeprefix("data:")
        data = base64.b64decode(b64, validate=True)
    except (ValueError, KeyError, AttributeError, binascii.Error):
        return JsonResponse({"error": "Invalid image data."}, status=400)
    try:
        text = ocr.transcribe_image(data, media_type)
    except ocr.OcrError as e:
        return JsonResponse({"error": str(e)}, status=400)
    with transaction.atomic():
        usage, _ = OcrUsage.objects.get_or_create(user=request.user, day=timezone.localdate())
        OcrUsage.objects.filter(pk=usage.pk).update(count=F("count") + 1)
    return JsonResponse({"text": text, "remaining": _ocr_remaining(request.user)})


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


def stored_file(request, name):
    """Serve an upload kept in the database (DatabaseStorage). Names are never reused
    (Django adds a suffix on clashes), so responses can be cached for a long time."""
    from django.utils.http import http_date

    from .models import StoredFile

    obj = get_object_or_404(StoredFile, name=name)
    etag = f'"{obj.pk}-{int(obj.updated_at.timestamp())}"'
    if request.headers.get("If-None-Match") == etag:
        resp = HttpResponse(status=304)
    else:
        resp = HttpResponse(bytes(obj.content), content_type=obj.content_type or "application/octet-stream")
        resp["Content-Length"] = obj.size
    resp["ETag"] = etag
    resp["Last-Modified"] = http_date(obj.updated_at.timestamp())
    resp["Cache-Control"] = "public, max-age=31536000, immutable"
    resp["X-Content-Type-Options"] = "nosniff"
    if not (obj.content_type or "").startswith("image/") or obj.content_type == "image/svg+xml":
        resp["Content-Disposition"] = "attachment"  # never render uploaded HTML/SVG inline
    return resp
