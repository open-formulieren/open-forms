from django.urls import path

from .views import AllAttributesListView, PluginListView, PluginOptionsView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="registrations-plugin-list"),
    path("plugin-options", PluginOptionsView.as_view(), name="registrations-plugin-list"),
    path(
        "attributes",
        AllAttributesListView.as_view(),
        name="registrations-attribute-list",
    ),
]
