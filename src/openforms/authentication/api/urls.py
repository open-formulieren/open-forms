from django.urls import path

from .views import AuthenticationLogoutView, PluginListView

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="authentication-plugin-list"),
    path("session", AuthenticationLogoutView.as_view(), name="logout"),
]
