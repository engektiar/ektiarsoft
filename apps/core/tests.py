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
        self.assertEqual(MenuItem.objects.count(), 13)  # 12 defaults + "Image to Text"
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


class InboxVisibilityTests(TestCase):
    def test_unread_contact_messages_are_visible_in_dashboard(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "Blue-River-42!x")
        self.client.post("/contact/", {"name": "Lead", "email": "lead@example.com", "subject": "Web app",
                                       "message": "Hi"})
        self.client.force_login(admin)
        page = self.client.get("/dashboard/requests/").content.decode()
        self.assertIn('class="side-badge"', page)                  # sidebar badge with unread count
        self.assertIn("1 new message from the website contact form", page)
        self.assertIn("Lead", self.client.get("/dashboard/m/messages/").content.decode())


class ImageToTextToolTests(TestCase):
    def test_tool_page_loads_with_ocr_engine_and_privacy_note(self):
        html = self.client.get("/image-to-text/").content.decode()
        self.assertIn("tesseract.js@", html)
        self.assertIn("never leaves it", html)  # free-mode privacy note
        self.assertIn('<option value="ben">', html)

    def test_menu_link_is_added_by_migration(self):
        self.assertTrue(MenuItem.objects.filter(url="/image-to-text/", location="header").exists())
        self.assertIn('href="/image-to-text/"', self.client.get("/").content.decode())

    def test_tool_is_in_sitemap_and_url_is_reserved(self):
        self.assertIn("/image-to-text/", self.client.get("/sitemap.xml").content.decode())
        from apps.core.models import RESERVED_SLUGS
        self.assertIn("image-to-text", RESERVED_SLUGS)

    def test_tool_has_no_server_side_upload(self):
        # the page must not post the image anywhere: no <form> with file upload on it
        html = self.client.get("/image-to-text/").content.decode()
        self.assertNotIn('enctype="multipart/form-data"', html)
        self.assertEqual(self.client.post("/image-to-text/").status_code, 405)


import base64 as _b64
import json as _json
from types import SimpleNamespace
from unittest import mock

from django.test import override_settings as _override


def _data_url(raw=None, kind="image/jpeg"):
    return f"data:{kind};base64," + _b64.b64encode(raw or png_bytes()).decode()


class _FakeClaude:
    """Stands in for anthropic.Anthropic - records the request, returns a canned reply."""
    last_kwargs = None

    def __init__(self, *a, stop_reason="end_turn", text="Name | MST TEST\nNID | 123", **kw):
        reply = SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])

        def create(**kwargs):
            _FakeClaude.last_kwargs = kwargs
            return reply
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=create))


class AiOcrTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ocr", "ocr@example.com", "abcdef")

    def post(self, body):
        return self.client.post("/image-to-text/ai/", data=_json.dumps(body), content_type="application/json")

    @mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_requires_login(self):
        self.assertEqual(self.post({"image": _data_url()}).status_code, 401)

    @mock.patch.dict("os.environ", {}, clear=False)
    def test_disabled_without_api_key(self):
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        self.client.force_login(self.user)
        self.assertEqual(self.post({"image": _data_url()}).status_code, 503)
        self.assertNotIn('value="ai"', self.client.get("/image-to-text/").content.decode())

    @mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "OCR_AI_DAILY_LIMIT": "2"})
    @mock.patch("anthropic.Anthropic", _FakeClaude)
    def test_success_request_shape_limit_and_nothing_stored(self):
        from apps.core.models import OcrUsage
        self.client.force_login(self.user)
        self.assertIn('value="ai"', self.client.get("/image-to-text/").content.decode())
        before = {m.__name__: m.objects.count() for m in (ContactMessage, StoredFile)}
        r = self.post({"image": _data_url()})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["text"], "Name | MST TEST\nNID | 123")
        self.assertEqual(r.json()["remaining"], 1)
        kw = _FakeClaude.last_kwargs
        self.assertEqual(kw["model"], "claude-opus-5-5")
        self.assertEqual(kw["fallbacks"], "default")
        self.assertIn("server-side-fallback-2026-07-01", kw["betas"])
        block = kw["messages"][0]["content"][0]
        self.assertEqual((block["type"], block["source"]["media_type"]), ("image", "image/jpeg"))
        # nothing but the usage counter is stored
        self.assertEqual(before, {m.__name__: m.objects.count() for m in (ContactMessage, StoredFile)})
        self.assertEqual(OcrUsage.objects.get(user=self.user).count, 1)
        self.post({"image": _data_url()})
        r = self.post({"image": _data_url()})
        self.assertEqual(r.status_code, 429)  # daily limit (2) reached

    @mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_bad_input_and_refusal(self):
        from apps.core.models import OcrUsage
        self.client.force_login(self.user)
        self.assertEqual(self.post({"image": "not-a-data-url"}).status_code, 400)
        self.assertEqual(self.post({"image": _data_url(kind="application/pdf")}).status_code, 400)
        self.assertEqual(self.post({"image": _data_url(b"x" * (4 * 1024 * 1024 + 1))}).status_code, 400)
        with mock.patch("anthropic.Anthropic", lambda *a, **k: _FakeClaude(stop_reason="refusal", text="")):
            r = self.post({"image": _data_url()})
        self.assertEqual(r.status_code, 400)
        self.assertIn("declined", r.json()["error"])
        self.assertFalse(OcrUsage.objects.filter(user=self.user, count__gt=0).exists())  # failures are not counted

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get("/image-to-text/ai/").status_code, 405)
