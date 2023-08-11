from django.urls import path

from .views import PrivacyPolicyInfoView, StatementsInfoListView

app_name = "config"

urlpatterns = [
    path(
        "privacy_policy_info",
        PrivacyPolicyInfoView.as_view(),
        name="privacy-policy-info",
    ),
    path(
        "statements-info-list",
        StatementsInfoListView.as_view(),
        name="statements-info-list",
    ),
]
