from django.urls import path

from .views import PrivacyPolicyView

app_name = "privacy-policy"

urlpatterns = [
    path("", PrivacyPolicyView.as_view(), name="privacy-policy"),
]
