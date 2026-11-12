"""Seed starter content: services, tech stack, pricing, FAQs, blog posts and
sample projects. Safe to run multiple times (skips existing records).

    python manage.py seed

Sample projects and testimonials are clearly labelled placeholders — replace
them with your real work from the dashboard before going live. Sample
testimonials are created UNPUBLISHED so no fake reviews appear on the site.
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.blog.models import Category, Post
from apps.core.models import FAQ, PricingPlan, Project, Service, SiteSetting, Technology, Testimonial

SERVICES = [
    ("Web Application Development", "web",
     "Custom, secure and scalable web applications built with Python, Django and modern JavaScript.",
     "Custom business web applications\nAdmin dashboards & CRMs\nE-commerce & payment integration\nREST & GraphQL APIs\nPerformance & security hardening",
     "I build web applications that solve real business problems — from internal tools and CRMs to customer-facing platforms.\n\n"
     "Every application is built on a solid architecture: clean Django backends, well-designed SQL databases, responsive interfaces and automated tests. "
     "You get software that is fast, secure, and easy to extend as your business grows."),
    ("SaaS Product Development", "cloud",
     "Multi-tenant SaaS platforms with subscriptions, roles & permissions, and analytics — from MVP to scale.",
     "MVP in weeks, not months\nMulti-user roles & permissions\nSubscription billing (Stripe & local gateways)\nCloud deployment & CI/CD\nAnalytics & reporting dashboards",
     "Turn your idea into a recurring-revenue product. I design and build SaaS platforms with multi-tenant architecture, "
     "role-based access control, subscription billing, onboarding flows and admin analytics.\n\n"
     "We start with a lean MVP to validate quickly, then iterate and scale on reliable cloud infrastructure."),
    ("Android App Development", "mobile",
     "Native and cross-platform Android apps with smooth UX, offline support and backend integration.",
     "Kotlin & Flutter apps\nAPI & Firebase integration\nPush notifications & offline mode\nPlay Store publishing\nMaintenance & updates",
     "I build Android apps your users will love — fast, intuitive and reliable. Whether it's a companion app for your web platform "
     "or a standalone product, I handle design, development, backend integration and Play Store launch."),
    ("Digital Marketing & SEO", "chart",
     "Technical SEO, content strategy and performance marketing that bring qualified traffic and leads.",
     "Technical SEO audits & fixes\nKeyword research & content strategy\nGoogle & Meta ads management\nAnalytics, tracking & conversion optimization\nMonthly growth reports",
     "Great software needs customers. I combine a developer's understanding of technical SEO with data-driven marketing — "
     "site speed, structured data, content strategy and paid campaigns — to grow traffic, leads and revenue."),
    ("API & System Integration", "api",
     "Connect your tools: payment gateways, ERPs, CRMs, SMS/email services and third-party APIs.",
     "REST API design & documentation\nPayment gateway integration\nThird-party API & webhook integration\nAutomation & background jobs\nData migration",
     "Make your systems talk to each other. I design clean, documented APIs and integrate payment gateways, CRMs, ERPs, "
     "messaging services and any third-party platform — automating manual work along the way."),
    ("UI/UX & Website Design", "design",
     "Modern, conversion-focused interfaces and responsive websites that look great on every device.",
     "Wireframes & interactive prototypes\nResponsive, mobile-first design\nDesign systems & component libraries\nLanding pages that convert\nAccessibility best practices",
     "Design is how your product feels. I create clean, modern interfaces with a focus on usability and conversion — "
     "from wireframes to pixel-perfect, responsive implementation."),
]

TECH = [
    ("Python", "backend", 95), ("Django", "backend", 95), ("Django REST Framework", "backend", 90),
    ("Node.js", "backend", 75), ("JavaScript", "frontend", 90), ("TypeScript", "frontend", 80),
    ("React", "frontend", 82), ("HTML5 & CSS3", "frontend", 95), ("Tailwind CSS", "frontend", 85),
    ("Kotlin", "mobile", 80), ("Flutter", "mobile", 78), ("Firebase", "mobile", 80),
    ("PostgreSQL", "database", 88), ("MySQL", "database", 90), ("Redis", "database", 75),
    ("Docker", "devops", 82), ("Linux & Nginx", "devops", 85), ("AWS / DigitalOcean", "devops", 78),
    ("Technical SEO", "marketing", 88), ("Google Analytics", "marketing", 85), ("Google & Meta Ads", "marketing", 78),
]

PLANS = [
    ("Starter", "$499", "/project", "For professional websites and landing pages.",
     "Up to 6 responsive pages\nSEO-optimized structure\nContact form & analytics\nAdmin panel to edit content\n1 month free support", False),
    ("Business", "$1,999", "/project", "For custom web apps and growing businesses.",
     "Custom web application\nUser accounts, roles & permissions\nDashboard & reporting\nAPI & payment integration\nDeployment + 3 months support", True),
    ("SaaS / Enterprise", "Custom", "", "For SaaS products, Android apps and complex systems.",
     "Full product discovery & architecture\nMulti-tenant SaaS / mobile apps\nSubscription billing\nCI/CD & cloud scaling\nDedicated ongoing support", False),
]

FAQS = [
    ("How long does a typical project take?",
     "A professional website usually takes 1–3 weeks. Custom web applications and SaaS MVPs typically take 4–12 weeks depending on scope. You'll get a detailed timeline with milestones before we start."),
    ("What technologies do you use?",
     "My core stack is Python and Django with PostgreSQL/MySQL databases, modern JavaScript on the frontend, and Kotlin/Flutter for Android. I choose tools based on what's best for your project."),
    ("Will my website be SEO-friendly and mobile responsive?",
     "Yes. Every project is mobile-first and built with SEO best practices: fast loading, semantic HTML, meta tags, structured data, XML sitemaps and clean URLs."),
    ("Do you provide support after launch?",
     "Absolutely. Every package includes free post-launch support, and I offer monthly maintenance plans for updates, security patches, backups and new features."),
    ("How do payments work?",
     "Projects are usually split into milestones — for example 40% to start, 40% at beta, and 20% on launch. Monthly plans are billed in advance."),
    ("Can I track the progress of my project?",
     "Yes. Create a client account to submit requests, see status updates and read notes on every project in your personal dashboard."),
]

PROJECTS = [
    ("Sample: Multi-tenant School Management SaaS", "saas",
     "Placeholder case study — a SaaS platform for schools with role-based portals for admins, teachers, students and parents.",
     "Django, PostgreSQL, Celery, Redis, Docker", True),
    ("Sample: E-commerce Web Application", "web",
     "Placeholder case study — an online store with inventory, payment gateway integration and a sales analytics dashboard.",
     "Django, MySQL, JavaScript, Stripe", True),
    ("Sample: Delivery Tracking Android App", "mobile",
     "Placeholder case study — an Android app for riders and customers with live order tracking and push notifications.",
     "Kotlin, Firebase, REST API", False),
    ("Sample: SEO Growth Campaign", "marketing",
     "Placeholder case study — technical SEO overhaul and content strategy for a service business website.",
     "Technical SEO, Google Analytics, Content Strategy", False),
    ("Sample: Business CRM & Invoicing System", "web",
     "Placeholder case study — a CRM with lead pipeline, invoicing, PDF reports and role-based team access.",
     "Django, PostgreSQL, HTMX, Chart.js", False),
    ("Sample: Restaurant POS & Booking SaaS", "saas",
     "Placeholder case study — a subscription POS with table booking, kitchen display and multi-branch reporting.",
     "Django REST, React, MySQL, Docker", False),
]

POSTS = [
    ("Development", "Why Django Is a Great Choice for Building SaaS Products",
     "django, saas, python",
     "<p>Choosing the right framework is one of the most important decisions when building a SaaS product. "
     "Django gives you a mature, secure and productive foundation.</p>"
     "<h2>Batteries included</h2><p>Authentication, an ORM, an admin panel, forms, security middleware and migrations come out of the box — "
     "so you spend your time on features your customers pay for.</p>"
     "<h2>Security by default</h2><p>Django protects against SQL injection, XSS, CSRF and clickjacking by default, which matters when you store customer data.</p>"
     "<h2>Scales with you</h2><p>With caching, background workers and a well-designed PostgreSQL or MySQL database, Django comfortably serves products from MVP to millions of requests.</p>"
     "<h2>Conclusion</h2><p>If you want to launch quickly without compromising on quality, Django is an excellent choice for your SaaS.</p>"),
    ("SEO", "Technical SEO Checklist for Developers",
     "seo, performance, web development",
     "<p>SEO isn't only about keywords — a large part of ranking well is technical. Here's a checklist I apply to every project.</p>"
     "<ul><li>Unique, descriptive <code>&lt;title&gt;</code> and meta description per page</li><li>Canonical URLs and clean, readable slugs</li>"
     "<li>XML sitemap and robots.txt</li><li>Structured data (JSON-LD) for your business, articles and FAQs</li>"
     "<li>Fast loading: compressed images, lazy loading, minimal JavaScript</li><li>Mobile-first, responsive design</li><li>HTTPS everywhere</li></ul>"
     "<p>Get these right and your content has a solid foundation to rank.</p>"),
    ("Business", "How to Plan Your First Web Application Project",
     "planning, startup, web application",
     "<p>A clear plan saves time and money. Before writing code, answer these questions:</p>"
     "<h2>1. What problem are you solving?</h2><p>Describe your users and the exact pain point. This keeps the scope focused.</p>"
     "<h2>2. What is the minimum viable product?</h2><p>List the few features that deliver the core value. Everything else can wait for version two.</p>"
     "<h2>3. Who needs access to what?</h2><p>Define user roles and permissions early — admins, staff, customers — so the system is designed for them from day one.</p>"
     "<h2>4. How will you measure success?</h2><p>Pick metrics such as sign-ups, orders or hours saved, and build tracking in from the start.</p>"),
]


class Command(BaseCommand):
    help = "Seed the database with starter website content."

    def handle(self, *args, **opts):
        SiteSetting.load()

        for i, (title, icon, short, features, body) in enumerate(SERVICES):
            Service.objects.get_or_create(title=title, defaults=dict(
                icon=icon, short_description=short, features=features, body=body, order=i,
                meta_description=short[:160]))

        for i, (name, cat, lvl) in enumerate(TECH):
            Technology.objects.get_or_create(name=name, defaults=dict(category=cat, proficiency=lvl, order=i))

        for i, (name, price, period, desc, feats, hl) in enumerate(PLANS):
            PricingPlan.objects.get_or_create(name=name, defaults=dict(
                price=price, period=period, description=desc, features=feats, is_highlighted=hl, order=i))

        for i, (q, a) in enumerate(FAQS):
            FAQ.objects.get_or_create(question=q, defaults=dict(answer=a, order=i))

        for title, cat, summary, stack, featured in PROJECTS:
            Project.objects.get_or_create(title=title, defaults=dict(
                category=cat, summary=summary, tech_stack=stack, is_featured=featured,
                body=summary + "\n\nReplace this sample with your real project: describe the challenge, "
                "your solution, the tech stack and measurable results.",
                completed_on=date.today()))

        if not Testimonial.objects.exists():
            Testimonial.objects.create(
                name="Sample Client", position="Replace me", company="Your client",
                quote="This is a placeholder testimonial. Add real client feedback from the dashboard and publish it.",
                is_published=False)

        for cat_name, title, tags, body in POSTS:
            cat, _ = Category.objects.get_or_create(name=cat_name)
            Post.objects.get_or_create(title=title, defaults=dict(
                category=cat, tags=tags, body=body, status=Post.PUBLISHED, published_at=timezone.now()))

        self.stdout.write(self.style.SUCCESS("Starter content seeded."))
