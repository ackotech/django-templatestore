from django.urls import path, re_path
from templatestore import views

urlpatterns = [
    # apis
    path("internal/api/v1/template/<slug:vendor>/channel/<slug:channel>/sync", views.sync_template_from_vendor),
    path("api/v1/template/<slug:vendor>/channel/<slug:channel>/sync", views.sync_template_manual),
    path("internal/api/v1/vendor/<slug:vendor>/channel/<slug:channel>/", views.get_vendor_template),
    path("internal/api/v1/vendor", views.vendor_view),
    path("api/v1/template", views.post_template_view),
    path("render_pdf", views.render_pdf),
    path("api/v1/render", views.render_template_view),
    path("api/v1/templates", views.get_templates_view),
    path("api/v2/templates", views.get_templates_view_v2),
    path("api/v1/tiny_url", views.save_tiny_url),
    path("internal/api/v1/template", views.post_template_view),
    re_path("api/v1/tiny_url/(?P<name>[a-zA-Z]+[a-zA-Z0-9_\-\s]+)/(?P<version>\d+\.\d+)$", views.get_tiny_url),
    re_path(
        "api/v1/template/(?P<name>[a-zA-Z]+[a-zA-Z0-9_\-\s]+)/versions$",
        views.get_template_versions_view,
    ),
    re_path(
        "api/v1/template/(?P<name>[a-zA-Z]+[a-zA-Z0-9_\-\s]+)/render",
        views.get_render_template_view,
    ),
    re_path(
        # "api/v1/template/(?P<name>[a-zA-Z]+[a-zA-Z0-9_]*)/(?P<version>\d+\.\d+)$",
        "api/v1/template/(?P<name>[a-zA-Z]+[a-zA-Z0-9_\-\s]+)/(?P<version>\d+\.\d+)$",
        views.get_template_details_view,
    ),
    re_path(
        "api/v1/template/(?P<name>[a-zA-Z]+[a-zA-Z0-9_\-\s]+)/(?P<version>\d+\.\d+)/render",
        views.get_render_template_view,
    ),
    re_path(
        "api/v1/template/(?P<name>[a-zA-Z]+[a-zA-Z0-9_\-\s]+)/attributes",
        views.patch_attributes_view,
    ),
    path("api/v1/config", views.get_config_view),
    # frontend
    re_path(r"^(?:.*)/?$", views.index, name="index"),
]
