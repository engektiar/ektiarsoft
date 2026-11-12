from django.contrib.sitemaps import Sitemap

from apps.blog.models import Post

from .models import PageContent, Project, Service


class _Base(Sitemap):
    protocol = "https"


class PageSitemap(_Base):
    """Built-in + custom pages that are published (managed in Dashboard -> Pages)."""
    changefreq = "monthly"

    def items(self):
        return PageContent.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        return 1.0 if obj.page == "home" else 0.8


class ServiceSitemap(_Base):
    changefreq = "monthly"
    priority = 0.9

    def items(self):
        return Service.objects.filter(is_active=True)


class ProjectSitemap(_Base):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Project.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class PostSitemap(_Base):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Post.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "pages": PageSitemap,
    "services": ServiceSitemap,
    "projects": ProjectSitemap,
    "blog": PostSitemap,
}
