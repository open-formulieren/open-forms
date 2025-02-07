from django.urls import include, path

from .views import AllAttributesListView, PluginListView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="registrations-plugin-list"),
    path(
        "attributes",
        AllAttributesListView.as_view(),
        name="registrations-attribute-list",
    ),
]

# add plugin URL patterns
# TODO: make this dynamic and include it through the registry?
urlpatterns += [
    path("plugins/camunda/", include("openforms.registrations.contrib.camunda.api")),
    path(
        "plugins/objects-api/",
        include("openforms.registrations.contrib.objects_api.api.urls"),
    ),
    path(
        "plugins/zgw-api/",
        include("openforms.registrations.contrib.zgw_apis.api.urls"),
    ),
    path(
        "plugins/json-dump/",
        include("openforms.registrations.contrib.json_dump.api.urls"),
    ),
]
