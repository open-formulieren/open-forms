from django.urls import path

from .views import PluginAttributesListView, PluginListView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="plugin-list"),
    path(
        "plugins/<slug:plugin>/attributes",
        PluginAttributesListView.as_view(),
        name="attribute-list",
    ),
]
