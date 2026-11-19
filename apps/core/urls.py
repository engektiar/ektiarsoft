from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path("portfolio/", views.portfolio, name="portfolio"),
    path("portfolio/<slug:slug>/", views.project_detail, name="project_detail"),
    path("pricing/", views.pricing, name="pricing"),
    path("contact/", views.contact, name="contact"),
    path("privacy-policy/", views.privacy, name="privacy"),
    path("image-to-text/", views.image_to_text, name="image_to_text"),
    path("image-to-text/ai/", views.image_to_text_ai, name="image_to_text_ai"),
    path("<slug:slug>/", views.custom_page, name="custom_page"),
]
