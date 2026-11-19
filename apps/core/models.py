from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def validate_image_size(file):
    from django.core.exceptions import ValidationError

    # 4 MB: Vercel rejects request bodies larger than 4.5 MB
    if file and getattr(file, "size", 0) > 4 * 1024 * 1024:
        raise ValidationError("Image is too large: maximum size is 4 MB.")


class SluggedModel(models.Model):
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(getattr(self, "title", "") or getattr(self, "name", ""))[:150] or "item"
            slug, i = base, 2
            while type(self).objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, i = f"{base}-{i}", i + 1
            self.slug = slug
        super().save(*args, **kwargs)


class SiteSetting(models.Model):
    """Singleton holding brand, contact and SEO defaults (edit from dashboard)."""

    site_name = models.CharField(max_length=80, default="EktiarSoft")
    owner_name = models.CharField(max_length=80, default="Your Name")
    job_title = models.CharField(max_length=120, default="Full-Stack Software Developer")
    tagline = models.CharField(
        max_length=200,
        default="I design, build and scale web apps, Android apps and digital growth systems.",
    )
    about = models.TextField(
        default=(
            "I'm a software developer with 5+ years of hands-on experience shipping "
            "production software — from SaaS platforms and business web applications "
            "to Android apps and data-driven digital marketing. I work across the full "
            "stack: Python/Django, JavaScript, REST APIs, SQL databases, cloud deployment "
            "and SEO, turning ideas into fast, secure and maintainable products."
        )
    )
    years_experience = models.PositiveIntegerField(default=5)
    email = models.EmailField(default="hello@example.com")
    phone = models.CharField(max_length=40, blank=True)
    whatsapp = models.CharField(
        max_length=40, blank=True,
        help_text="Your WhatsApp number, e.g. 01628414116 or +8801628414116. Shows a floating chat button.",
    )
    address = models.CharField(max_length=200, default="Dhaka, Bangladesh")
    available_for_work = models.BooleanField(default=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    meta_title = models.CharField(
        max_length=70, default="Full-Stack Software Developer | Web, Android & SaaS"
    )
    meta_description = models.CharField(
        max_length=160,
        default=(
            "Software developer with 5+ years of experience building web applications, "
            "SaaS platforms, Android apps and SEO-driven digital marketing solutions."
        ),
    )
    meta_keywords = models.CharField(
        max_length=255,
        default="software developer, web application development, django developer, "
        "android app development, SaaS development, digital marketing, SEO",
    )
    header_cta_text = models.CharField("header button text", max_length=40, default="Hire Me", blank=True)
    header_cta_url = models.CharField("header button link", max_length=255, default="/contact/", blank=True)
    response_time = models.CharField(max_length=60, default="Within 24 hours", blank=True)
    footer_note = models.CharField(max_length=120, default="Built with Python · Django · SQL", blank=True)
    google_analytics_id = models.CharField(max_length=30, blank=True, help_text="e.g. G-XXXXXXX")
    photo = models.ImageField(
        "profile photo", upload_to="profile/", blank=True, validators=[validate_image_size],
        help_text="Your photo: square works best (e.g. 800×800 px, JPG/PNG/WebP, under 4 MB). "
                  "Shown in About sections and on blog posts.",
    )
    resume = models.FileField(upload_to="resume/", blank=True)

    class Meta:
        verbose_name = "site setting"
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        self.whatsapp = self.normalize_whatsapp(self.whatsapp)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_whatsapp(value):
        """'01628-414116' / '+880 1628 414116' -> '8801628414116' (digits, country code)."""
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if digits.startswith("00"):
            digits = digits[2:]
        if len(digits) == 11 and digits.startswith("01"):  # Bangladeshi local mobile format
            digits = "88" + digits
        return digits

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Service(SluggedModel):
    ICONS = [
        ("web", "Web"), ("mobile", "Mobile"), ("cloud", "Cloud / SaaS"), ("chart", "Marketing"),
        ("api", "API"), ("design", "Design"), ("db", "Database"), ("shield", "Security"),
    ]
    title = models.CharField(max_length=120)
    icon = models.CharField(max_length=20, choices=ICONS, default="web")
    short_description = models.CharField(max_length=220)
    body = models.TextField(blank=True)
    features = models.TextField(blank=True, help_text="One feature per line.")
    meta_description = models.CharField(max_length=160, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:service_detail", args=[self.slug])

    @property
    def feature_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]


class Technology(models.Model):
    CATEGORIES = [
        ("backend", "Backend"), ("frontend", "Frontend"), ("mobile", "Mobile"),
        ("database", "Database"), ("devops", "DevOps & Cloud"), ("marketing", "Marketing"),
    ]
    name = models.CharField(max_length=60)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    proficiency = models.PositiveIntegerField(default=80, help_text="0-100")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "name"]
        verbose_name_plural = "technologies"

    def __str__(self):
        return self.name


class Project(SluggedModel):
    CATEGORIES = [
        ("web", "Web App"), ("saas", "SaaS"), ("mobile", "Android App"),
        ("marketing", "Digital Marketing"), ("other", "Other"),
    ]
    title = models.CharField(max_length=160)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="web")
    client = models.CharField(max_length=120, blank=True)
    summary = models.CharField(max_length=260)
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to="projects/", blank=True)
    tech_stack = models.CharField(max_length=255, blank=True, help_text="Comma separated")
    live_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    completed_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-completed_on", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:project_detail", args=[self.slug])

    @property
    def stack_list(self):
        return [t.strip() for t in self.tech_stack.split(",") if t.strip()]


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=120, blank=True)
    company = models.CharField(max_length=120, blank=True)
    quote = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    is_published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-id"]

    def __str__(self):
        return f"{self.name} — {self.company}"


class PricingPlan(models.Model):
    name = models.CharField(max_length=60)
    price = models.CharField(max_length=30, help_text='e.g. "$499" or "Custom"')
    period = models.CharField(max_length=30, blank=True, help_text='e.g. "/project"')
    description = models.CharField(max_length=200, blank=True)
    features = models.TextField(help_text="One feature per line.")
    is_highlighted = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]


class FAQ(models.Model):
    question = models.CharField(max_length=220)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=160)
    budget = models.CharField(max_length=40, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.subject}"


class ServiceRequest(models.Model):
    """Client-portal project request (the SaaS side: clients log in & track)."""

    STATUS = [
        ("new", "New"), ("review", "In review"), ("quoted", "Quoted"),
        ("progress", "In progress"), ("done", "Completed"), ("cancelled", "Cancelled"),
    ]
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="service_requests"
    )
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=160)
    description = models.TextField()
    budget = models.CharField(max_length=40, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="new")
    admin_note = models.TextField(blank=True, help_text="Visible to the client.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [("manage_servicerequest", "Can manage all client requests")]

    def __str__(self):
        return self.title


RESERVED_SLUGS = {
    "admin", "accounts", "dashboard", "blog", "about", "services", "portfolio", "pricing",
    "contact", "privacy-policy", "static", "media", "files", "home", "sitemap", "robots", "image-to-text",
}


class PageContent(models.Model):
    """A website page: hero heading + SEO + an ordered list of Sections.

    Built-in pages (home, about, ...) have fixed URLs; "custom" pages are created
    from the dashboard and served at /<slug>/.
    The hero heading renders as:  <heading> <highlight in gradient> <heading_end>
    On Home, ``highlight`` is a comma-separated list of rotating (typed) words.
    """

    BUILTIN = [
        ("home", "Home"), ("about", "About"), ("services", "Services"), ("portfolio", "Portfolio"),
        ("pricing", "Pricing"), ("contact", "Contact"), ("blog", "Blog"),
    ]
    PAGES = BUILTIN + [("custom", "Custom page")]
    URL_NAMES = {
        "home": "core:home", "about": "core:about", "services": "core:services",
        "portfolio": "core:portfolio", "pricing": "core:pricing", "contact": "core:contact",
        "blog": "blog:list",
    }
    DEFAULTS = {
        "home": dict(eyebrow="Available for new projects", heading="I build",
                     highlight="web applications, SaaS platforms, Android apps, growth engines, custom software",
                     heading_end="that move business forward.",
                     button_text="Start your project", button_url="/contact/",
                     button2_text="View my work", button2_url="/portfolio/"),
        "about": dict(eyebrow="About me", heading="Engineer by craft,", highlight="partner by choice.",
                      meta_title="About me — Full-Stack Software Developer"),
        "services": dict(eyebrow="Services", heading="Everything you need to", highlight="build & grow",
                         heading_end="online.",
                         lead="One partner for strategy, design, development, launch and marketing.",
                         meta_title="Services — Web, SaaS, Android & Digital Marketing",
                         meta_description="Custom web application development, SaaS platforms, Android apps, "
                                          "API integrations and SEO-driven digital marketing."),
        "portfolio": dict(eyebrow="Portfolio", heading="Work that", highlight="speaks for itself.",
                          lead="A selection of products, platforms and campaigns I've designed, built and launched.",
                          meta_title="Portfolio — Web Apps, SaaS & Android Projects",
                          meta_description="Case studies and projects: web applications, SaaS platforms, "
                                           "Android apps and digital marketing campaigns."),
        "pricing": dict(eyebrow="Pricing", heading="Invest in software that", highlight="pays for itself.",
                        lead="Clear packages to start from — every proposal is tailored to your goals and budget.",
                        meta_title="Pricing — Website, SaaS & App Development Packages",
                        meta_description="Transparent pricing for websites, web applications, SaaS platforms, "
                                         "Android apps and digital marketing. Get a free custom quote."),
        "contact": dict(eyebrow="Contact", heading="Let's talk about", highlight="your project.",
                        lead="Share a few details and I'll get back to you within 24 hours with next steps.",
                        meta_title="Contact — Hire a Software Developer",
                        meta_description="Start your web app, SaaS, Android or digital marketing project. "
                                         "Get a free consultation and quote."),
        "blog": dict(eyebrow="Blog", heading="Notes on", highlight="code, product & growth.",
                     lead="Tutorials, case studies and lessons from building real software.",
                     meta_title="Blog — Software Development & Digital Marketing Insights",
                     meta_description="Practical articles on web development, Django, SaaS, Android apps, "
                                      "SEO and digital marketing."),
    }

    page = models.CharField("page type", max_length=20, choices=PAGES, default="custom")
    title = models.CharField("page name", max_length=100, blank=True,
                             help_text="Internal name, also used in the breadcrumb.")
    slug = models.SlugField("URL", max_length=80, unique=True, null=True, blank=True,
                            help_text="Custom pages are served at /<url>/. Leave blank to generate from the name.")
    is_published = models.BooleanField("published", default=True)
    show_hero = models.BooleanField("show page header", default=True)
    eyebrow = models.CharField("small label above heading", max_length=80, blank=True)
    heading = models.CharField("heading (plain part)", max_length=150, blank=True)
    highlight = models.CharField(
        "heading (gradient part)", max_length=255, blank=True,
        help_text="Shown in gradient colour. On Home: comma-separated words that rotate with a typing effect.",
    )
    heading_end = models.CharField("heading (ending)", max_length=150, blank=True,
                                   help_text="Optional text after the gradient part.")
    lead = models.TextField("intro paragraph", blank=True,
                            help_text="Leave blank on Home/About to use the automatic text from Site Settings.")
    button_text = models.CharField("header button text", max_length=60, blank=True)
    button_url = models.CharField("header button link", max_length=255, blank=True)
    button2_text = models.CharField("second button text", max_length=60, blank=True)
    button2_url = models.CharField("second button link", max_length=255, blank=True)
    meta_title = models.CharField("SEO title", max_length=70, blank=True,
                                  help_text="Browser tab & Google title. Blank = automatic.")
    meta_description = models.CharField("SEO description", max_length=160, blank=True,
                                        help_text="Google snippet text. Blank = automatic.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "page"
        verbose_name_plural = "pages"

    def __str__(self):
        return self.title or self.get_page_display()

    @property
    def is_builtin(self):
        return self.page != "custom"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.page == "custom":
            slug = self.slug or slugify(self.title)
            if not slug:
                raise ValidationError({"title": "Give the page a name."})
            if slug in RESERVED_SLUGS:
                raise ValidationError({"slug": f'"{slug}" is reserved, choose another URL.'})

    def save(self, *args, **kwargs):
        if self.page == "custom" and not self.slug:
            base = slugify(self.title)[:70] or "page"
            slug, i = base, 2
            while PageContent.objects.filter(slug=slug).exclude(pk=self.pk).exists() or slug in RESERVED_SLUGS:
                slug, i = f"{base}-{i}", i + 1
            self.slug = slug
        if not self.title:
            self.title = self.get_page_display()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.page in self.URL_NAMES:
            return reverse(self.URL_NAMES[self.page])
        return reverse("core:custom_page", args=[self.slug])

    @classmethod
    def get(cls, page):
        obj = cls.objects.filter(page=page).first()
        if obj is None:
            obj = cls.objects.create(page=page, slug=page, title=dict(cls.BUILTIN).get(page, page),
                                     **cls.DEFAULTS.get(page, {}))
        return obj

    @property
    def typed_words(self):
        return [w.strip() for w in self.highlight.split(",") if w.strip()]


class Section(models.Model):
    """One block on a page. Turn on/off, reorder and edit from Dashboard -> Pages."""

    KINDS = [
        ("Website data", [
            ("services", "Services grid"), ("projects", "Portfolio projects (featured)"),
            ("portfolio_grid", "Portfolio: all projects with filters"), ("pricing", "Pricing plans"),
            ("testimonials", "Testimonials"), ("faq", "FAQ"), ("blog_posts", "Latest blog posts"),
            ("blog_list", "Blog list with search (blog page)"), ("tech_marquee", "Tech stack ticker"),
            ("skills", "Skill bars"), ("contact_form", "Contact form"),
        ]),
        ("Custom content", [
            ("cards", "Feature cards"), ("process", "Process / steps"), ("about", "Text + image with checklist"),
            ("stats", "Stats / numbers"), ("text", "Rich text"), ("cta", "Call to action banner"),
            ("html", "Custom HTML / embed"),
        ]),
    ]
    STYLES = [("default", "Default"), ("alt", "Alternate background"), ("tight", "No top spacing")]

    _HEAD = ["eyebrow", "title", "highlight", "title_end"]
    # which form fields each section type uses (the dashboard shows only these)
    FIELDS = {
        "services": _HEAD + ["subtitle", "button_text", "button_url", "limit", "show_details"],
        "projects": _HEAD + ["subtitle", "button_text", "button_url", "limit"],
        "portfolio_grid": _HEAD + ["subtitle"],
        "pricing": _HEAD + ["subtitle"],
        "testimonials": _HEAD + ["subtitle", "limit"],
        "faq": _HEAD + ["subtitle", "limit"],
        "blog_posts": _HEAD + ["subtitle", "button_text", "button_url", "limit"],
        "blog_list": _HEAD,
        "tech_marquee": [],
        "skills": _HEAD + ["subtitle"],
        "contact_form": ["title", "subtitle", "items"],
        "cards": _HEAD + ["subtitle", "items"],
        "process": _HEAD + ["subtitle", "items"],
        "about": _HEAD + ["body", "image", "items", "button_text", "button_url", "button2_text",
                          "button2_url", "show_details"],
        "stats": _HEAD + ["subtitle", "items"],
        "text": _HEAD + ["body"],
        "cta": _HEAD + ["subtitle", "button_text", "button_url", "button2_text", "button2_url"],
        "html": ["body"],
    }
    ITEM_HELP = {
        "cards": "One card per line:  icon | Title | Description   (icons: web, mobile, cloud, chart, api, "
                 "design, db, shield, zap, clock, rocket, search, star, users)",
        "process": "One step per line:  icon | Title | Description",
        "about": "Checklist, one per line:  Bold text | rest of the sentence",
        "stats": "One stat per line:  Number | Label   (e.g.  5+ | Years experience)",
        "contact_form": "'What happens next' steps, one per line:  Title | Description",
    }

    page = models.ForeignKey(PageContent, on_delete=models.CASCADE, related_name="sections")
    kind = models.CharField("section type", max_length=20, choices=KINDS)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField("visible", default=True)
    style = models.CharField(max_length=10, choices=STYLES, default="default")
    eyebrow = models.CharField("small label", max_length=80, blank=True)
    title = models.CharField("heading", max_length=150, blank=True)
    highlight = models.CharField("heading (gradient part)", max_length=150, blank=True)
    title_end = models.CharField("heading (ending)", max_length=150, blank=True)
    subtitle = models.TextField("intro text", blank=True)
    body = models.TextField("content", blank=True, help_text="HTML allowed.")
    image = models.ImageField(upload_to="sections/", blank=True)
    items = models.TextField("items", blank=True)
    button_text = models.CharField(max_length=60, blank=True)
    button_url = models.CharField(max_length=255, blank=True)
    button2_text = models.CharField("second button text", max_length=60, blank=True)
    button2_url = models.CharField("second button URL", max_length=255, blank=True)
    limit = models.PositiveSmallIntegerField("number of items", default=6, help_text="0 = show all")
    show_details = models.BooleanField("show extra details", default=False,
                                       help_text="Services: show feature list. About: show experience badge.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page", "order", "id"]

    def __str__(self):
        label = self.title or self.highlight or ""
        return f"{self.get_kind_display()}{': ' + label if label else ''}"

    @property
    def rows(self):
        """items -> [[part, part, ...], ...] split on '|'."""
        return [[p.strip() for p in line.split("|")] for line in self.items.splitlines() if line.strip()]


class MenuItem(models.Model):
    LOCATIONS = [("header", "Header menu"), ("footer", "Footer: Company column")]
    location = models.CharField(max_length=10, choices=LOCATIONS, default="header")
    label = models.CharField(max_length=60)
    url = models.CharField("link", max_length=255, help_text="e.g. /about/ or https://...")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField("visible", default=True)
    new_tab = models.BooleanField("open in new tab", default=False)

    class Meta:
        ordering = ["location", "order", "id"]
        verbose_name = "menu link"
        verbose_name_plural = "menu links"

    def __str__(self):
        return f"{self.label} ({self.get_location_display()})"


class StoredFile(models.Model):
    """Uploaded file kept inside the database (used on Vercel, which has no disk).
    Served at /files/<name> by apps.core.views.stored_file."""

    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "stored file"

    def __str__(self):
        return self.name


class OcrUsage(models.Model):
    """How many AI text extractions a user made on a day (for the daily limit).
    Only the count is stored - never the image or the extracted text."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ocr_usage")
    day = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("user", "day")]
        verbose_name = "AI OCR usage"

    def __str__(self):
        return f"{self.user} {self.day}: {self.count}"
