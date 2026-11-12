from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission


class RoleBackend(ModelBackend):
    """Authenticate by username OR email; add role permissions to the user.

    Works with Django's standard ``user.has_perm()``, ``@permission_required``
    and ``{% if perms.app.codename %}`` in templates.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if username and "@" in username:
            user = User.objects.filter(email__iexact=username).first()
            if user:
                username = user.get_username()
        return super().authenticate(request, username=username, password=password, **kwargs)

    def _get_role_permissions(self, user_obj):
        role = getattr(user_obj, "role", None)
        if role is None:
            return Permission.objects.none()
        if role.grants_all:
            return Permission.objects.all()
        return role.permissions.all()

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        if not hasattr(user_obj, "_role_perm_cache"):
            perms = self._get_role_permissions(user_obj).values_list(
                "content_type__app_label", "codename"
            )
            user_obj._role_perm_cache = {f"{app}.{code}" for app, code in perms}
        return {*super().get_all_permissions(user_obj, obj), *user_obj._role_perm_cache}
