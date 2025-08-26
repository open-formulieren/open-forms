from django.urls import include, path

from .views import PluginAttributesListView, PluginListView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="prefill-plugin-list"),
    path(
        "plugins/<slug:plugin>/attributes",
        PluginAttributesListView.as_view(),
        name="prefill-attribute-list",
    ),
]

# add plugin URL patterns
# TODO: make this dynamic and include it through the registry?
urlpatterns += [
    path(
        "plugins/objects-api/",
        include("openforms.prefill.contrib.objects_api.api.urls"),
    ),
    path(
        "plugins/yivi/",
        include("openforms.prefill.contrib.yivi.api.urls"),
    ),
]
