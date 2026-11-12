"""Automatic RBAC bootstrapping.

* After every ``migrate`` the default roles are created/updated and their
  permission sets are synced (new models => new permissions picked up).
* Every new user automatically receives the default role.
* Superusers automatically receive the Super Admin role.
"""
from django.conf import settings
from django.contrib.auth.models import Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

# codename patterns per role. "app.*" = all perms of an app,
# "app.view_*" = all view perms of an app, or exact "app.codename".
DEFAULT_ROLES = {
    "super-admin": {
        "name": "Super Admin",
        "description": "Full, unrestricted access to everything.",
        "grants_all": True,
        "perms": [],
    },
    "admin": {
        "name": "Admin",
        "description": "Manages content, users, messages and client requests.",
        "perms": [
            "accounts.access_dashboard", "accounts.manage_users", "accounts.view_user",
            "accounts.change_user", "accounts.add_user", "accounts.view_role",
            "accounts.manage_site_settings", "core.*", "blog.*",
        ],
    },
    "editor": {
        "name": "Editor",
        "description": "Writes blog posts and manages portfolio content.",
        "perms": [
            "accounts.access_dashboard", "blog.*", "core.add_project", "core.change_project",
            "core.view_project", "core.view_service", "core.view_testimonial",
            "core.view_pagecontent", "core.change_pagecontent",
        ],
    },
    "client": {
        "name": "Client",
        "description": "Customers: can submit and track project requests.",
        "default": True,
        "perms": ["accounts.access_dashboard", "core.add_servicerequest", "core.view_servicerequest"],
    },
}


def _resolve(patterns):
    qs = Permission.objects.select_related("content_type")
    result = []
    for perm in qs:
        full = f"{perm.content_type.app_label}.{perm.codename}"
        for p in patterns:
            if p == full:
                result.append(perm)
                break
            if p.endswith("*"):
                prefix = p[:-1]
                if full.startswith(prefix):
                    result.append(perm)
                    break
    return result


@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    # run after the last app with models so every permission already exists
    if sender.label != "blog":
        return
    from .models import Role

    for slug, cfg in DEFAULT_ROLES.items():
        role, created = Role.objects.get_or_create(
            slug=slug,
            defaults={
                "name": cfg["name"],
                "description": cfg["description"],
                "is_system": True,
                "grants_all": cfg.get("grants_all", False),
            },
        )
        if created:
            role.permissions.set(_resolve(cfg["perms"]))
            if cfg.get("default") and not Role.objects.filter(is_default=True).exists():
                role.is_default = True
                role.save()

    # make sure some role is default
    if not Role.objects.filter(is_default=True).exists():
        r = Role.objects.filter(slug=settings.DEFAULT_USER_ROLE).first()
        if r:
            r.is_default = True
            r.save()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def assign_role(sender, instance, created, **kwargs):
    if not created or instance.role_id:
        return
    from .models import Role

    role = (
        Role.objects.filter(slug="super-admin").first()
        if instance.is_superuser
        else Role.get_default()
    )
    if role:
        type(instance).objects.filter(pk=instance.pk).update(role=role)
        instance.role = role
