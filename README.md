# DevStudio — Personal Software-Developer Website (Django + SQL)

A personal portfolio and software-studio website with a built-in multi-user SaaS dashboard.

## Features

**Public website (SEO-ready, responsive)**
- Home: typing hero, code window, tech marquee, services, process, portfolio, pricing, testimonials, blog, FAQ, CTA
- About (skills bars), Services + service detail pages, Portfolio with filters + case studies, Pricing, Contact form (with spam honeypot), Blog (categories, tags, search, pagination), Privacy policy, custom 404/500 pages
- Light/dark theme, mobile menu, scroll animations; respects reduced-motion
- SEO: per-page title, meta description and canonical URL, Open Graph/Twitter cards, JSON-LD (Person, ProfessionalService, Service, BlogPosting, FAQPage, Breadcrumb), `sitemap.xml`, `robots.txt`, clean slugs, optional Google Analytics

**Page builder / CMS (`/dashboard/` → Website)**
- **Pages & Sections:** every page, built-in or new (served at `/<url>/`), is an ordered list of sections. Each section can be switched on or off, reordered, edited or deleted. There are 18 section types: data-driven ones (services, projects, pricing, testimonials, FAQ, blog, skills, contact form…) and custom ones (cards, process steps, text + image, stats, rich text, CTA, custom HTML).
- Page header (heading, gradient part, intro, buttons) and SEO title/description are editable per page. A page can be unpublished with one switch; its menu links and buttons then disappear automatically.
- **Menu Links** for the header and footer. Header button, footer note and response time live in **Site Settings**.
- Every yes/no column in every dashboard list is an instant on/off switch. Empty sections are never rendered, so no blank gaps.
- Default sections live in `apps/core/defaults.py`. Section templates are in `templates/sections/`.

**SaaS dashboard (`/dashboard/`)**
- Multi-user accounts: register, log in with username or email, profile and avatar, password change
- **Dynamic roles and permissions (RBAC):** create roles in the UI and tick permissions grouped by module. Every user has one role, and permissions apply instantly through a custom auth backend (`apps/accounts/backends.py`).
- **Automatic setup:** after `migrate`, the default roles (Super Admin, Admin, Editor, Client) are created with their permissions. New sign-ups get the default role, and superusers get Super Admin.
- Client portal: clients submit project requests and track status/notes; staff manage all requests
- Content management for blog posts, categories, portfolio, services, tech stack, testimonials, pricing, FAQs, contact inbox, users, roles and site settings (brand, contact, SEO)
- A generic CRUD engine (`apps/dashboard/resources.py`): to give a model a dashboard section, add one `Resource(...)` line

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env            # then edit values
python manage.py migrate        # also creates default roles automatically
python manage.py seed           # starter content (services, plans, FAQ, posts, sample projects)
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000. The dashboard is at `/dashboard/` and Django admin is at `/admin/`.

## Database

The database name is set by `DB_NAME` (default `portfolio`).

| `DB_ENGINE` | Notes |
|---|---|
| `sqlite` | File `portfolio.sqlite3`. Zero setup. Currently active. |
| `mysql` | Needs **MySQL 8+ or MariaDB 10.6+** (Django 6 requirement). XAMPP ships MariaDB 10.4, so upgrade it first or use MySQL on your host. The `portfolio` database already exists in XAMPP MySQL. Driver: PyMySQL. |
| `postgresql` | Install `psycopg[binary]`. |

To move the existing data to MySQL:
```bash
python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission > data.json
# set DB_ENGINE=mysql in .env
python manage.py migrate && python manage.py loaddata data.json
```

## Before going live

1. Set your real details in **Dashboard → Site Settings**: name, email, socials and SEO text.
2. Replace the **"Sample:"** portfolio projects with your real work. Add real testimonials; the sample testimonial is unpublished.
3. In `.env`: `DEBUG=False`, a new `SECRET_KEY`, `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`, `CSRF_TRUSTED_ORIGINS=https://yourdomain.com`, `SITE_URL=https://yourdomain.com`
4. `python manage.py collectstatic` (WhiteNoise serves static files). Run with `gunicorn config.wsgi` behind Nginx, with HTTPS.
5. Submit `https://yourdomain.com/sitemap.xml` to Google Search Console.

## Project structure

```
config/            settings, urls, wsgi
apps/accounts/     User, Role, RoleBackend, auto-role signals, auth views
apps/core/         public pages, content models, SEO sitemaps, seed command
apps/blog/         posts & categories
apps/dashboard/    generic permission-aware CRUD, client portal, icons tag lib
templates/         base (SEO), public pages, dashboard
static/            css (main, dashboard), js, img
```
