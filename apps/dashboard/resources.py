"""Registry that powers the generic, permission-aware CRUD dashboard.

Add a new model to the dashboard by adding one ``Resource`` entry below —
list/search/create/edit/delete pages and sidebar link are generated, and
access is enforced with the model's standard Django permissions
(``view_``/``add_``/``change_``/``delete_``), which are granted via Roles.
"""
from dataclasses import dataclass, field

from django import forms

from apps.accounts.forms import RoleForm, UserAdminForm
from apps.accounts.models import Role, User
from apps.blog.models import Category, Post

from .forms import SectionForm
from apps.core.models import (
    FAQ, ContactMessage, MenuItem, PageContent, PricingPlan, Section, Project, Service, SiteSetting, Technology, Testimonial,
)


@dataclass
class Resource:
    key: str
    model: type
    label: str
    icon: str
    group: str
    list_display: list
    fields: list = field(default_factory=list)
    form_class: type | None = None
    search_fields: list = field(default_factory=list)
    readonly_fields: list = field(default_factory=list)
    form_template: str = "dashboard/form.html"
    perm_override: str | None = None  # single perm controlling all actions
    can_add: bool = True
    can_delete: bool = True
    in_nav: bool = True
    # protect(obj, action, user) -> error message (str) to block "toggle:<field>" / "delete"
    protect: object = None

    def blocked(self, obj, action, user):
        return self.protect(obj, action, user) if self.protect else None

    def is_toggle(self, name):
        """Boolean columns in the list are rendered as on/off switches."""
        try:
            return self.opts.get_field(name).get_internal_type() == "BooleanField"
        except Exception:
            return False

    @property
    def opts(self):
        return self.model._meta

    def perm(self, action):
        if self.perm_override:
            return self.perm_override
        return f"{self.opts.app_label}.{action}_{self.opts.model_name}"

    def allowed(self, user, action):
        return user.has_perm(self.perm(action))

    def get_form_class(self):
        if self.form_class:
            return self.form_class
        widgets = {}
        for f in self.fields:
            mf = self.opts.get_field(f)
            if mf.get_internal_type() == "TextField":
                widgets[f] = forms.Textarea(attrs={"rows": 6})
            elif mf.get_internal_type() == "DateField":
                widgets[f] = forms.DateInput(attrs={"type": "date"})
            elif mf.get_internal_type() == "DateTimeField":
                widgets[f] = forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")

        class _Form(forms.ModelForm):
            class Meta:
                model = self.model
                fields = self.fields

            def __init__(s, *a, **kw):
                super().__init__(*a, **kw)
                for name, fld in s.fields.items():
                    w = fld.widget
                    if name in widgets:
                        fld.widget = widgets[name]
                        w = fld.widget
                    if not isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                        w.attrs.setdefault("class", "input")

        return _Form


def _protect_page(obj, action, user):
    if action == "delete" and obj.is_builtin:
        return "Built-in pages can't be deleted. Switch them off (unpublish) instead."
    if action == "toggle:is_published" and obj.page == "home":
        return "The Home page must stay published."
    return None


def _protect_user(obj, action, user):
    if action == "toggle:is_active" and obj.pk == user.pk:
        return "You can't deactivate your own account."
    return None


def _protect_role(obj, action, user):
    if action == "delete" and obj.is_system:
        return "System roles cannot be deleted."
    if action == "toggle:is_system":
        return "The system flag is fixed."
    if action == "toggle:is_default" and obj.is_default:
        return "Make another role the default instead (switch it on there)."
    return None


RESOURCES = [
    Resource("pages", PageContent, "Pages & Sections", "layers", "Website",
             ["title", "page", "slug", "show_hero", "is_published", "updated_at"],
             ["title", "slug", "is_published", "show_hero", "eyebrow", "heading", "highlight", "heading_end",
              "lead", "meta_title", "meta_description"],
             search_fields=["title", "heading"], protect=_protect_page),
    Resource("sections", Section, "Sections", "layers", "Website",
             ["kind", "title", "is_active", "order"], form_class=SectionForm,
             form_template="dashboard/section_form.html", in_nav=False),
    Resource("menu", MenuItem, "Menu Links", "menu", "Website",
             ["label", "url", "location", "order", "is_active"],
             ["location", "label", "url", "order", "is_active", "new_tab"], search_fields=["label", "url"]),
    Resource("posts", Post, "Blog Posts", "pen", "Content",
             ["title", "category", "status", "published_at", "views"],
             ["title", "slug", "category", "tags", "excerpt", "body", "cover", "status",
              "published_at", "meta_title", "meta_description"],
             search_fields=["title", "body"]),
    Resource("categories", Category, "Blog Categories", "folder", "Content",
             ["name", "slug"], ["name", "slug", "description"], search_fields=["name"]),
    Resource("projects", Project, "Portfolio", "grid", "Content",
             ["title", "category", "is_featured", "is_published"],
             ["title", "slug", "category", "client", "summary", "body", "image", "tech_stack",
              "live_url", "repo_url", "is_featured", "is_published", "completed_on"],
             search_fields=["title", "summary"]),
    Resource("services", Service, "Services", "layers", "Content",
             ["title", "icon", "order", "is_active"],
             ["title", "slug", "icon", "short_description", "body", "features",
              "meta_description", "order", "is_active"], search_fields=["title"]),
    Resource("technologies", Technology, "Tech Stack", "cpu", "Content",
             ["name", "category", "proficiency"], ["name", "category", "proficiency", "order"],
             search_fields=["name"]),
    Resource("testimonials", Testimonial, "Testimonials", "star", "Content",
             ["name", "company", "rating", "is_published"],
             ["name", "position", "company", "quote", "rating", "is_published", "order"]),
    Resource("plans", PricingPlan, "Pricing Plans", "tag", "Content",
             ["name", "price", "is_highlighted", "is_active"],
             ["name", "price", "period", "description", "features", "is_highlighted", "order", "is_active"]),
    Resource("faqs", FAQ, "FAQs", "help", "Content",
             ["question", "order", "is_active"], ["question", "answer", "order", "is_active"]),
    Resource("messages", ContactMessage, "Inbox", "mail", "CRM",
             ["name", "email", "subject", "is_read", "created_at"], ["is_read"],
             search_fields=["name", "email", "subject"],
             readonly_fields=["name", "email", "phone", "subject", "budget", "message", "created_at"],
             can_add=False),
    Resource("users", User, "Users", "users", "Access Control",
             ["username", "email", "role", "is_active", "date_joined"],
             form_class=UserAdminForm, search_fields=["username", "email", "first_name"],
             perm_override="accounts.manage_users", protect=_protect_user),
    Resource("roles", Role, "Roles & Permissions", "shield", "Access Control",
             ["name", "description", "is_default", "is_system"],
             form_class=RoleForm, form_template="dashboard/role_form.html",
             perm_override="accounts.manage_roles", protect=_protect_role),
]

REGISTRY = {r.key: r for r in RESOURCES}

SETTINGS_FIELDS = ["photo"] + [f.name for f in SiteSetting._meta.fields if f.name not in ("id", "photo")]
