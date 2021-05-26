from django.urls import path

from .views import PluginListView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="plugin-list"),
]
