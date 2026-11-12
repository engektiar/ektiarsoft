"""Default sections + menu links. Used by the migration that introduced the
page builder, so a fresh site looks complete. Everything here is editable
from Dashboard -> Pages and Dashboard -> Menu Links afterwards."""

CTA = dict(
    kind="cta", eyebrow="Let's build together", title="Have an idea? Let's turn it into",
    highlight="great software.",
    subtitle="Tell me about your web app, Android app, SaaS product or growth goals. You'll get a clear "
             "plan, timeline and quote, usually within 24 hours.",
    button_text="Start a project", button_url="/contact/",
    button2_text="Open client portal", button2_url="/accounts/register/",
)

DEFAULT_SECTIONS = {
    "home": [
        dict(kind="tech_marquee"),
        dict(kind="services", eyebrow="What I do", title="End-to-end software services,",
             highlight="one expert partner.",
             subtitle="From the first wireframe to deployment and growth marketing: everything a software "
                      "company delivers, with the focus of a dedicated developer.",
             button_text="All services", button_url="/services/", limit=6),
        dict(kind="process", style="alt", eyebrow="How I work", title="A proven process that",
             highlight="ships on time.",
             subtitle="Transparent milestones, weekly demos, and a client portal where you can track every request.",
             items="search | Discover | We define goals, users, scope and success metrics together.\n"
                   "design | Design | Architecture, database schema and pixel-perfect UI prototypes.\n"
                   "api | Develop | Agile sprints with clean, tested, documented code.\n"
                   "rocket | Launch & Grow | Deployment, monitoring, SEO and ongoing support."),
        dict(kind="projects", eyebrow="Selected work", title="Products I've", highlight="designed & built.",
             button_text="Full portfolio", button_url="/portfolio/", limit=6),
        dict(kind="about", style="alt", eyebrow="Why work with me", title="Agency-level delivery,",
             highlight="developer-level care.", show_details=True,
             items="Full-stack ownership | backend, frontend, mobile, database and DevOps.\n"
                   "Business-first thinking | software built around revenue, not just features.\n"
                   "SEO & performance baked in | fast pages that rank and convert.\n"
                   "Long-term support | maintenance, scaling and new features after launch.",
             button_text="More about me", button_url="/about/"),
        dict(kind="pricing", eyebrow="Pricing", title="Simple,", highlight="transparent", title_end="packages.",
             subtitle="Every project is unique. These are starting points; get an exact quote for free."),
        dict(kind="testimonials", style="alt", eyebrow="Client feedback", title="What clients",
             highlight="say.", limit=6),
        dict(kind="blog_posts", eyebrow="From the blog", title="Insights on", highlight="code & growth.",
             button_text="All articles", button_url="/blog/", limit=3),
        dict(kind="faq", style="alt", eyebrow="FAQ", title="Questions,", highlight="answered.", limit=6),
        CTA,
    ],
    "about": [
        dict(kind="about", style="tight", eyebrow="My story", title="Hi, I'm", highlight="", show_details=True,
             body="<p>I work like a complete software company in one: planning, UI/UX, backend, mobile, QA, "
                  "deployment and marketing. You get a single accountable partner and a product that's "
                  "built to grow.</p>",
             button_text="Work with me", button_url="/contact/"),
        dict(kind="skills", style="alt", eyebrow="Skills & stack", title="Tools I use to",
             highlight="ship great products."),
        dict(kind="cards", eyebrow="Values", title="How I approach", highlight="every project.",
             items="shield | Quality & security | Clean architecture, code reviews, automated tests and "
                   "security best practices by default.\n"
                   "clock | Clear communication | Regular updates, honest timelines and a client portal so "
                   "you always know where things stand.\n"
                   "chart | Measurable results | Every feature tied to a business outcome: more users, more "
                   "sales, less manual work."),
        dict(kind="testimonials", style="alt", eyebrow="Testimonials", title="Trusted by",
             highlight="clients.", limit=0),
        CTA,
    ],
    "services": [
        dict(kind="services", style="tight", limit=0, show_details=True),
        dict(kind="pricing", style="alt", eyebrow="Packages", title="Choose a", highlight="starting point."),
        dict(kind="faq", eyebrow="FAQ", title="Common", highlight="questions.", limit=0),
        CTA,
    ],
    "portfolio": [dict(kind="portfolio_grid", style="tight"), CTA],
    "pricing": [
        dict(kind="pricing", style="tight"),
        dict(kind="faq", style="alt", eyebrow="FAQ", title="Pricing", highlight="questions.", limit=0),
        CTA,
    ],
    "contact": [
        dict(kind="contact_form", style="tight", title="Send a message",
             subtitle="Tell me a little about your project. I'll reply with next steps within 24 hours.",
             items="I review your message | and reply within 24 hours with questions or ideas.\n"
                   "Free discovery call | a short call to understand your goals, users and timeline.\n"
                   "Clear proposal & quote | scope, milestones and a fixed price, no surprises."),
    ],
    "blog": [dict(kind="blog_list", style="tight")],
}

DEFAULT_MENU = {
    "header": [("Home", "/"), ("About", "/about/"), ("Services", "/services/"), ("Portfolio", "/portfolio/"),
               ("Pricing", "/pricing/"), ("Blog", "/blog/"), ("Contact", "/contact/")],
    "footer": [("About", "/about/"), ("Portfolio", "/portfolio/"), ("Pricing", "/pricing/"),
               ("Blog", "/blog/"), ("Privacy Policy", "/privacy-policy/")],
}
