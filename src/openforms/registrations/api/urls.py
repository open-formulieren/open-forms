from django.urls import include, path

from .views import AllAttributesListView, InformatieObjectTypenListView, PluginListView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="registrations-plugin-list"),
    path(
        "attributes",
        AllAttributesListView.as_view(),
        name="registrations-attribute-list",
    ),
    path(
        "informatieobjecttypen",
        InformatieObjectTypenListView.as_view(),
        name="iotypen-list",
    ),
]


# add plugin URL patterns
# TODO: make this dynamic and include it through the registry?
urlpatterns += [
    path("plugins/camunda/", include("openforms.registrations.contrib.camunda.api")),
]
