from django.urls import path

from .views import DeclarationsInfoListView, PrivacyPolicyInfoView

app_name = "config"

urlpatterns = [
    path(
        "privacy_policy_info",
        PrivacyPolicyInfoView.as_view(),
        name="privacy-policy-info",
    ),
    path(
        "declarations_info_list",
        DeclarationsInfoListView.as_view(),
        name="declarations-info-list",
    ),
]
