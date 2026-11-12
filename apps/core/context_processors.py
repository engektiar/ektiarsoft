from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from .models import MenuItem, PageContent, Service, SiteSetting


def site(request):
    try:
        cfg = SiteSetting.load()
        nav_services = list(Service.objects.filter(is_active=True)[:8])
        hidden = {p.get_absolute_url() for p in PageContent.objects.filter(is_published=False)}
        menu = [m for m in MenuItem.objects.filter(is_active=True) if m.url not in hidden]
    except (OperationalError, ProgrammingError):  # before first migrate
        cfg, nav_services, menu, hidden = SiteSetting(), [], [], set()
    return {
        "site": cfg,
        "nav_services": nav_services,
        "header_menu": [m for m in menu if m.location == "header"],
        "footer_menu": [m for m in menu if m.location == "footer"],
        "hidden_urls": hidden,
        "SITE_URL": settings.SITE_URL,
        "canonical_url": settings.SITE_URL + request.path,
    }
