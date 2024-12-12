from django.urls import path

from .views import AnalyticsToolsConfigurationView

app_name = "analytics_tools"

urlpatterns = [
    path(
        "analytics-tools-config-info",
        AnalyticsToolsConfigurationView.as_view(),
        name="analytics-tools-config-info",
    ),
]
