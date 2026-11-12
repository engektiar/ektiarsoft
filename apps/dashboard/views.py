from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts.models import Role, User
from apps.blog.models import Post
from apps.core.forms import ServiceRequestForm
from apps.core.models import ContactMessage, PageContent, Project, Section, ServiceRequest, SiteSetting

from .forms import PageForm
from .resources import REGISTRY, RESOURCES, SETTINGS_FIELDS


def _nav(user):
    groups = {}
    for r in RESOURCES:
        if r.in_nav and r.allowed(user, "view"):
            groups.setdefault(r.group, []).append(r)
    return groups


def _ctx(request, **extra):
    return {"nav_groups": _nav(request.user), **extra}


def _resource(key, user, action):
    res = REGISTRY.get(key)
    if not res:
        raise Http404
    if not res.allowed(user, action):
        raise PermissionDenied
    return res


def _next(request, fallback):
    """Redirect target from ?next= / POST next, only if it is a safe local URL."""
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return nxt
    return fallback


@login_required
def home(request):
    u = request.user
    ctx = {"section": "home"}
    if u.has_perm("core.manage_servicerequest") or u.has_perm("accounts.manage_users"):
        ctx.update(
            stat_users=User.objects.count(),
            stat_posts=Post.objects.count(),
            stat_projects=Project.objects.count(),
            stat_unread=ContactMessage.objects.filter(is_read=False).count(),
            stat_requests=ServiceRequest.objects.exclude(status__in=["done", "cancelled"]).count(),
            recent_messages=ContactMessage.objects.all()[:5],
            recent_requests=ServiceRequest.objects.select_related("client")[:5],
            roles=Role.objects.all(),
            is_staff_view=True,
        )
    else:
        ctx.update(my_requests=u.service_requests.all()[:5])
    return render(request, "dashboard/home.html", _ctx(request, **ctx))


# ---------------------------------------------------------------- generic CRUD
@login_required
def resource_list(request, key):
    res = _resource(key, request.user, "view")
    qs = res.model.objects.all()
    if not qs.ordered:
        qs = qs.order_by("-pk")
    q = request.GET.get("q", "").strip()
    if q and res.search_fields:
        cond = Q()
        for f in res.search_fields:
            cond |= Q(**{f"{f}__icontains": q})
        qs = qs.filter(cond)
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    can_change = res.allowed(request.user, "change")
    rows = []
    for obj in page:
        cells = []
        for c in res.list_display:
            value = getattr(obj, f"get_{c}_display", lambda o=obj, c=c: getattr(o, c))()
            toggle = can_change and res.is_toggle(c)
            locked = res.blocked(obj, f"toggle:{c}", request.user) if toggle else None
            cells.append({"name": c, "value": value, "toggle": toggle, "locked": locked})
        deletable = not res.blocked(obj, "delete", request.user)
        rows.append((obj, cells, deletable))
    headers = [res.opts.get_field(c).verbose_name for c in res.list_display]
    return render(request, "dashboard/list.html", _ctx(
        request, res=res, rows=rows, headers=headers, page_obj=page, q=q, section=key,
        can_add=res.can_add and res.allowed(request.user, "add"),
        can_change=can_change,
        can_delete=res.can_delete and res.allowed(request.user, "delete"),
    ))


@login_required
@require_POST
def resource_toggle(request, key, pk, field):
    """Flip a boolean field (Active / Inactive switch). Returns JSON for fetch() calls."""
    res = _resource(key, request.user, "change")
    if field not in res.list_display + res.fields + ["is_active"] or not res.is_toggle(field):
        raise Http404
    obj = get_object_or_404(res.model, pk=pk)
    error = res.blocked(obj, f"toggle:{field}", request.user)
    if not error:
        setattr(obj, field, not getattr(obj, field))
        obj.save(update_fields=[field] + (["updated_at"] if hasattr(obj, "updated_at") else []))
    value = getattr(obj, field)
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"ok": not error, "value": value, "error": error}, status=400 if error else 200)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, f"“{obj}” is now {'ON' if value else 'OFF'}.")
    return redirect(_next(request, reverse("dashboard:list", args=[key])))


@login_required
def resource_form(request, key, pk=None):
    res = _resource(key, request.user, "change" if pk else "add")
    if not pk and not res.can_add:
        raise PermissionDenied
    obj = get_object_or_404(res.model, pk=pk) if pk else None
    Form = res.get_form_class()
    initial = {k: v for k, v in request.GET.items() if k in ("page", "kind")} if not obj else None
    form = Form(request.POST or None, request.FILES or None, instance=obj, initial=initial)
    if request.method == "POST" and form.is_valid():
        instance = form.save(commit=False)
        if key == "posts" and not instance.author_id:
            instance.author = request.user
        instance.save()
        form.save_m2m()
        messages.success(request, f"{res.opts.verbose_name.title()} saved.")
        if key == "pages" and not obj:
            return redirect("dashboard:page_edit", pk=instance.pk)
        return redirect(_next(request, reverse("dashboard:list", args=[key])))
    if obj and key == "messages" and not obj.is_read:
        ContactMessage.objects.filter(pk=obj.pk).update(is_read=True)
    readonly = [(res.opts.get_field(f).verbose_name, getattr(obj, f)) for f in res.readonly_fields] if obj else []
    return render(request, res.form_template, _ctx(
        request, res=res, form=form, obj=obj, readonly=readonly, section="pages" if key == "sections" else key,
        next=_next(request, ""),
    ))


@login_required
def resource_delete(request, key, pk):
    res = _resource(key, request.user, "delete")
    if not res.can_delete:
        raise PermissionDenied
    obj = get_object_or_404(res.model, pk=pk)
    back = _next(request, reverse("dashboard:list", args=[key]))
    error = res.blocked(obj, "delete", request.user)
    if key == "users" and obj.pk == request.user.pk:
        error = "You cannot delete your own account."
    if error:
        messages.error(request, error)
        return redirect(back)
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, f"{res.opts.verbose_name.title()} deleted.")
        except ProtectedError:
            messages.error(request, "This item is in use and cannot be deleted.")
        return redirect(back)
    return render(request, "dashboard/confirm_delete.html", _ctx(
        request, res=res, obj=obj, section="pages" if key == "sections" else key, back=back,
    ))


# ---------------------------------------------------------------- page builder
@login_required
def page_edit(request, pk):
    if not request.user.has_perm("core.change_pagecontent"):
        raise PermissionDenied
    page = get_object_or_404(PageContent, pk=pk)
    form = PageForm(request.POST or None, instance=page)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Page saved.")
        return redirect("dashboard:page_edit", pk=pk)
    from apps.core.templatetags.sections import _is_empty, section_data

    sections = list(page.sections.all())
    for s in sections:
        s.empty = _is_empty(s, section_data(s, {}))
    return render(request, "dashboard/page_edit.html", _ctx(
        request, page=page, form=form, sections=sections, kinds=Section.KINDS, section="pages",
        can_add_section=request.user.has_perm("core.add_section"),
        can_change_section=request.user.has_perm("core.change_section"),
        can_delete_section=request.user.has_perm("core.delete_section"),
    ))


@login_required
@require_POST
def section_move(request, pk, direction):
    if not request.user.has_perm("core.change_section"):
        raise PermissionDenied
    sec = get_object_or_404(Section, pk=pk)
    siblings = list(sec.page.sections.all())
    for i, s in enumerate(siblings):  # normalise order values first
        if s.order != (i + 1) * 10:
            Section.objects.filter(pk=s.pk).update(order=(i + 1) * 10)
            s.order = (i + 1) * 10
    idx = next(i for i, s in enumerate(siblings) if s.pk == sec.pk)
    j = idx - 1 if direction == "up" else idx + 1
    if 0 <= j < len(siblings):
        a, b = siblings[idx], siblings[j]
        Section.objects.filter(pk=a.pk).update(order=b.order)
        Section.objects.filter(pk=b.pk).update(order=a.order)
    return redirect(reverse("dashboard:page_edit", args=[sec.page_id]) + f"#sec-{sec.pk}")


# ---------------------------------------------------------------- site settings
@login_required
def site_settings(request):
    if not request.user.has_perm("accounts.manage_site_settings"):
        raise PermissionDenied
    Form = forms.modelform_factory(SiteSetting, fields=SETTINGS_FIELDS)
    form = Form(request.POST or None, request.FILES or None, instance=SiteSetting.load())
    for name, f in form.fields.items():
        if not isinstance(f.widget, forms.CheckboxInput):
            f.widget.attrs["class"] = "input"
        if isinstance(f.widget, forms.Textarea):
            f.widget.attrs["rows"] = 5
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Site settings updated.")
        return redirect("dashboard:settings")
    return render(request, "dashboard/settings.html", _ctx(request, form=form, section="settings"))


# ---------------------------------------------------------------- client portal
@login_required
def requests_list(request):
    u = request.user
    manage = u.has_perm("core.manage_servicerequest")
    if not (manage or u.has_perm("core.view_servicerequest")):
        raise PermissionDenied
    qs = ServiceRequest.objects.select_related("client", "service")
    if not manage:
        qs = qs.filter(client=u)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    return render(request, "dashboard/requests.html", _ctx(
        request, requests=qs, manage=manage, statuses=ServiceRequest.STATUS,
        status=status, section="requests",
        can_add=u.has_perm("core.add_servicerequest"),
    ))


@login_required
def request_create(request):
    if not request.user.has_perm("core.add_servicerequest"):
        raise PermissionDenied
    form = ServiceRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        sr = form.save(commit=False)
        sr.client = request.user
        sr.save()
        messages.success(request, "Request submitted! You can track its status here.")
        return redirect("dashboard:requests")
    return render(request, "dashboard/request_form.html", _ctx(request, form=form, section="requests"))


class _StatusForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ("status", "admin_note")
        widgets = {"admin_note": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"


@login_required
def request_detail(request, pk):
    u = request.user
    manage = u.has_perm("core.manage_servicerequest")
    sr = get_object_or_404(ServiceRequest.objects.select_related("client", "service"), pk=pk)
    if not manage and sr.client_id != u.pk:
        raise PermissionDenied
    form = _StatusForm(request.POST or None, instance=sr) if manage else None
    if form and request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Request updated.")
        return redirect("dashboard:request_detail", pk=pk)
    return render(request, "dashboard/request_detail.html", _ctx(
        request, sr=sr, form=form, section="requests",
    ))
