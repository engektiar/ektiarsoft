"""Site-wide regression tests.  Run:  python manage.py test

Each run builds a brand-new database from the migrations, so these tests also
prove that a fresh database (e.g. a new Vercel/Neon database) sets up correctly.
"""
import io
import re

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.accounts.models import Role, User
from apps.core.models import (
    FAQ, ContactMessage, MenuItem, PageContent, Section, Service, SiteSetting, StoredFile,
)

FETCH = {"HTTP_X_REQUESTED_WITH": "fetch"}


def png_bytes(color=(20, 120, 200)):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buf, "PNG")
    return buf.getvalue()


class FreshDatabaseTests(TestCase):
    def test_default_content_is_created_by_migrations(self):
        self.assertEqual(PageContent.objects.filter(page="custom").count(), 0)
        self.assertEqual(
            sorted(PageContent.objects.values_list("page", flat=True)),
            sorted(k for k, _ in PageContent.BUILTIN))
        self.assertEqual(Section.objects.count(), 26)
        self.assertEqual(MenuItem.objects.count(), 12)
        self.assertEqual(set(Role.objects.values_list("slug", flat=True)), {"super-admin", "admin", "editor", "client"})
        self.assertEqual(PageContent.get("home").button_text, "Start your project")


class PublicSiteTests(TestCase):
    def test_public_pages_load(self):
        for url in ["/", "/about/", "/services/", "/portfolio/", "/pricing/", "/contact/", "/blog/",
                    "/privacy-policy/", "/sitemap.xml", "/robots.txt", "/accounts/login/", "/accounts/register/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_page_is_404(self):
        self.assertEqual(self.client.get("/no-such-page/").status_code, 404)

    def test_empty_sections_are_not_rendered(self):
        html = self.client.get("/").content.decode()
        testimonials = Section.objects.get(page__page="home", kind="testimonials")
        self.assertNotIn(f'id="section-{testimonials.pk}"', html)  # no testimonials -> no blank gap

    def test_login_page_shows_site_settings(self):
        html = self.client.get("/accounts/login/").content.decode()
        self.assertIn(SiteSetting.load().owner_name, html)

    def test_whatsapp_number_is_normalised_and_shown(self):
        s = SiteSetting.load()
        s.whatsapp = "01628-414116"
        s.save()
        self.assertEqual(SiteSetting.load().whatsapp, "8801628414116")
        html = self.client.get("/").content.decode()
        self.assertIn("wa.me/8801628414116", html)
        self.assertIn("+880 1628-414116", html)

    def test_contact_form_saves_message(self):
        r = self.client.post("/contact/", {"name": "A", "email": "a@example.com", "subject": "Hi",
                                           "message": "Hello", "budget": "5k+"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ContactMessage.objects.filter(email="a@example.com").exists())

    def test_contact_form_honeypot_blocks_spam(self):
        self.client.post("/contact/", {"name": "B", "email": "b@example.com", "subject": "x",
                                       "message": "spam", "website": "http://spam"})
        self.assertFalse(ContactMessage.objects.filter(email="b@example.com").exists())


class AccountsAndRolesTests(TestCase):
    def test_registration_gives_default_client_role(self):
        self.client.post("/accounts/register/", {
            "first_name": "Test", "last_name": "User", "username": "tuser", "email": "t@example.com",
            "password1": "Blue-River-42!x", "password2": "Blue-River-42!x"})
        self.assertEqual(User.objects.get(username="tuser").role.slug, "client")

    def test_superuser_gets_super_admin_role(self):
        u = User.objects.create_superuser("boss", "boss@example.com", "Blue-River-42!x")
        u.refresh_from_db()
        self.assertEqual(u.role.slug, "super-admin")

    def test_client_cannot_manage_users_or_roles(self):
        u = User.objects.create_user("c1", "c1@example.com", "Blue-River-42!x")
        self.client.force_login(u)
        self.assertEqual(self.client.get("/dashboard/").status_code, 200)
        self.assertEqual(self.client.get("/dashboard/m/users/").status_code, 403)
        self.assertEqual(self.client.get("/dashboard/m/roles/").status_code, 403)

    def test_editor_can_edit_pages(self):
        u = User.objects.create_user("ed", "ed@example.com", "Blue-River-42!x")
        u.role = Role.objects.get(slug="editor")
        u.save()
        self.client.force_login(u)
        self.assertEqual(self.client.get(f"/dashboard/m/pages/{PageContent.get('home').pk}/").status_code, 200)


class DashboardCmsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "Blue-River-42!x")
        self.client.force_login(self.admin)

    def test_all_dashboard_lists_load(self):
        for key in ["pages", "menu", "posts", "categories", "projects", "services", "technologies",
                    "testimonials", "plans", "faqs", "messages", "users", "roles"]:
            with self.subTest(key=key):
                self.assertEqual(self.client.get(f"/dashboard/m/{key}/").status_code, 200)

    def test_section_switch_hides_and_shows(self):
        sec = Section.objects.get(page__page="home", kind="process")
        r = self.client.post(f"/dashboard/m/sections/{sec.pk}/toggle/is_active/", **FETCH)
        self.assertFalse(r.json()["value"])
        self.assertNotIn(f'id="section-{sec.pk}"', self.client.get("/").content.decode())
        self.client.post(f"/dashboard/m/sections/{sec.pk}/toggle/is_active/", **FETCH)
        self.assertIn(f'id="section-{sec.pk}"', self.client.get("/").content.decode())

    def test_unpublished_page_is_hidden_from_visitors_and_menu(self):
        about = PageContent.get("about")
        self.client.post(f"/dashboard/m/pages/{about.pk}/toggle/is_published/", **FETCH)
        self.client.logout()
        self.assertEqual(self.client.get("/about/").status_code, 404)
        self.assertNotIn('href="/about/"', self.client.get("/").content.decode())

    def test_protections(self):
        home = PageContent.get("home")
        r = self.client.post(f"/dashboard/m/pages/{home.pk}/toggle/is_published/", **FETCH)
        self.assertEqual(r.status_code, 400)
        self.client.post(f"/dashboard/m/pages/{home.pk}/delete/")
        self.assertTrue(PageContent.objects.filter(pk=home.pk).exists())
        r = self.client.post(f"/dashboard/m/users/{self.admin.pk}/toggle/is_active/", **FETCH)
        self.assertEqual(r.status_code, 400)
        admin_role = Role.objects.get(slug="admin")
        self.client.post(f"/dashboard/m/roles/{admin_role.pk}/delete/")
        self.assertTrue(Role.objects.filter(pk=admin_role.pk).exists())

    def test_add_move_edit_delete_section(self):
        home = PageContent.get("home")
        r = self.client.post("/dashboard/m/sections/add/", {
            "page": home.pk, "kind": "stats", "is_active": "on", "style": "default", "order": 999,
            "title": "Results that", "highlight": "speak.", "limit": 6, "items": "5+ | Years"})
        self.assertEqual(r.status_code, 302)
        new = Section.objects.get(page=home, kind="stats")
        self.assertIn("Results that", self.client.get("/").content.decode())
        first, second = list(home.sections.values_list("pk", flat=True))[:2]
        self.client.post(f"/dashboard/sections/{second}/move/up/")
        self.assertEqual(list(home.sections.values_list("pk", flat=True))[0], second)
        self.client.post(f"/dashboard/m/sections/{new.pk}/delete/")
        self.assertFalse(Section.objects.filter(pk=new.pk).exists())

    def test_custom_page_and_reserved_urls(self):
        self.client.post("/dashboard/m/pages/add/", {"title": "Careers", "is_published": "on", "show_hero": "on",
                                                     "heading": "Join", "highlight": "us."})
        page = PageContent.objects.get(page="custom", title="Careers")
        self.assertEqual(page.slug, "careers")
        self.assertEqual(self.client.get("/careers/").status_code, 200)
        for reserved in ["blog", "files"]:
            r = self.client.post("/dashboard/m/pages/add/", {"title": "X", "slug": reserved, "is_published": "on"})
            self.assertContains(r, "reserved")

    def test_faq_switch_hides_question(self):
        faq = FAQ.objects.create(question="Unique test question?", answer="Yes.")
        self.assertIn(faq.question, self.client.get("/").content.decode())
        self.client.post(f"/dashboard/m/faqs/{faq.pk}/toggle/is_active/", **FETCH)
        self.assertNotIn(faq.question, self.client.get("/").content.decode())

    def test_dates_are_formatted(self):
        self.assertNotIn("+00:00", self.client.get("/dashboard/m/pages/").content.decode())


@override_settings(STORAGES={
    "default": {"BACKEND": "apps.core.storage.DatabaseStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class DatabaseMediaTests(TestCase):
    """Uploads stored inside the database (how the site runs on Vercel)."""

    def test_upload_store_and_serve_photo(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "Blue-River-42!x")
        self.client.force_login(admin)
        s = SiteSetting.load()
        data = {f.name: getattr(s, f.name) for f in s._meta.fields if f.name not in ("id", "photo", "resume")}
        data = {k: ("on" if v is True else v) for k, v in data.items() if v is not False and v is not None}
        r = self.client.post("/dashboard/settings/", {**data, "photo": SimpleUploadedFile("me.png", png_bytes(), "image/png")})
        self.assertEqual(r.status_code, 302)
        s = SiteSetting.load()
        self.assertTrue(StoredFile.objects.filter(name=s.photo.name).exists())
        url = s.photo.url
        self.assertTrue(url.startswith("/files/"))
        r = self.client.get(url)
        self.assertEqual((r.status_code, r["Content-Type"]), (200, "image/png"))
        self.assertEqual(r.content, png_bytes())
        self.assertEqual(self.client.get(url, HTTP_IF_NONE_MATCH=r["ETag"]).status_code, 304)
        self.assertIn(url, self.client.get("/about/").content.decode())

    def test_oversized_and_fake_images_rejected(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "Blue-River-42!x")
        self.client.force_login(admin)
        s = SiteSetting.load()
        data = {f.name: getattr(s, f.name) for f in s._meta.fields if f.name not in ("id", "photo", "resume")}
        data = {k: ("on" if v is True else v) for k, v in data.items() if v is not False and v is not None}
        for upload in [SimpleUploadedFile("big.png", b"\x89PNG" + b"0" * (5 * 1024 * 1024), "image/png"),
                       SimpleUploadedFile("x.png", b"not an image", "image/png")]:
            self.client.post("/dashboard/settings/", {**data, "photo": upload})
        self.assertEqual(StoredFile.objects.count(), 0)

    def test_uploaded_svg_is_not_rendered_inline(self):
        StoredFile.objects.create(name="x/evil.svg", content=b"<svg onload=alert(1)>", content_type="image/svg+xml", size=20)
        r = self.client.get("/files/x/evil.svg")
        self.assertEqual(r["Content-Disposition"], "attachment")
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")

    def test_missing_file_is_404(self):
        self.assertEqual(self.client.get("/files/none.jpg").status_code, 404)


class StatsAndMarkupTests(TestCase):
    def test_hero_stats_show_real_numbers(self):
        Service.objects.create(title="Test service", short_description="x")
        html = self.client.get("/").content.decode()
        self.assertTrue(re.search(r'data-count="\d+">\d+</span>', html))
