from django.urls import path

from .views import PrivacyPolicyInfoView

app_name = "config"

urlpatterns = [
    path(
        "privacy-policy-info",
        PrivacyPolicyInfoView.as_view(),
        name="privacy-policy-info",
    ),
]
