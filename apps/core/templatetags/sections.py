"""{% render_section section %} — renders templates/sections/<kind>.html with the
data that section type needs (services, projects, plans, ...)."""
from django import template

from apps.blog.models import Post
from apps.core.models import FAQ, PricingPlan, Project, Service, Technology, Testimonial

register = template.Library()


def _limit(qs, n):
    return qs[:n] if n else qs


def section_data(section, context):
    k, n = section.kind, section.limit
    if k == "services":
        return {"services": _limit(Service.objects.filter(is_active=True), n)}
    if k == "projects":
        return {"projects": _limit(Project.objects.filter(is_published=True), n)}
    if k == "portfolio_grid":
        return {"projects": Project.objects.filter(is_published=True), "categories": Project.CATEGORIES}
    if k == "pricing":
        return {"plans": PricingPlan.objects.filter(is_active=True)}
    if k == "testimonials":
        return {"testimonials": _limit(Testimonial.objects.filter(is_published=True), n)}
    if k == "faq":
        return {"faqs": _limit(FAQ.objects.filter(is_active=True), n)}
    if k == "blog_posts":
        return {"posts": Post.objects.published()[: n or 3]}
    if k == "tech_marquee":
        return {"technologies": Technology.objects.all()}
    if k == "skills":
        groups = {}
        for t in Technology.objects.all():
            groups.setdefault(t.get_category_display(), []).append(t)
        return {"tech_groups": groups}
    if k == "contact_form":
        from apps.core.forms import ContactForm

        return {"form": context.get("contact_form") or ContactForm()}
    return {}


# the data key that must be non-empty for a section to be shown at all
_REQUIRED = {
    "services": "services", "projects": "projects", "pricing": "plans", "testimonials": "testimonials",
    "faq": "faqs", "blog_posts": "posts", "tech_marquee": "technologies", "skills": "tech_groups",
}


def _is_empty(section, data):
    key = _REQUIRED.get(section.kind)
    if key is not None:
        value = data.get(key)
        return not (value.exists() if hasattr(value, "exists") else value)
    if section.kind in ("cards", "process", "stats"):
        return not section.rows
    if section.kind in ("text", "html"):
        return not section.body.strip() and not (section.title or section.highlight)
    return False


@register.simple_tag(takes_context=True)
def render_section(context, section):
    """Render one section — or nothing at all if it has no content (no blank gaps)."""
    data = section_data(section, context)
    if _is_empty(section, data):
        return ""
    tpl = context.template.engine.get_template(f"sections/{section.kind}.html")
    with context.push(section=section, **data):
        return tpl.render(context)
