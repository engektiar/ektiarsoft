from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("settings/", views.site_settings, name="settings"),
    path("requests/", views.requests_list, name="requests"),
    path("requests/new/", views.request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("m/pages/<int:pk>/", views.page_edit, name="page_edit"),
    path("sections/<int:pk>/move/<str:direction>/", views.section_move, name="section_move"),
    path("m/<slug:key>/", views.resource_list, name="list"),
    path("m/<slug:key>/add/", views.resource_form, name="add"),
    path("m/<slug:key>/<int:pk>/", views.resource_form, name="edit"),
    path("m/<slug:key>/<int:pk>/delete/", views.resource_delete, name="delete"),
    path("m/<slug:key>/<int:pk>/toggle/<str:field>/", views.resource_toggle, name="toggle"),
]
