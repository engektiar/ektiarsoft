from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils.text import slugify


class Role(models.Model):
    """A named bundle of permissions. Every user gets exactly one role.

    Roles are fully dynamic: create a role from the dashboard, tick the
    permissions it should grant, and every user holding the role gets them
    immediately (resolved by ``apps.accounts.backends.RoleBackend``).
    """

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    is_default = models.BooleanField(
        default=False, help_text="Automatically assigned to newly registered users."
    )
    is_system = models.BooleanField(
        default=False, help_text="System roles cannot be deleted."
    )
    grants_all = models.BooleanField(
        default=False, help_text="Super role: grants every permission automatically."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        if self.is_default:
            Role.objects.using(self._state.db or "default").exclude(pk=self.pk).filter(
                is_default=True).update(is_default=False)

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_default=True).first()


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        permissions = [
            ("access_dashboard", "Can access the dashboard"),
            ("manage_roles", "Can create and edit roles & permissions"),
            ("manage_users", "Can manage users"),
            ("manage_site_settings", "Can edit site settings"),
        ]

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        name = self.display_name
        parts = name.split()
        return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()
