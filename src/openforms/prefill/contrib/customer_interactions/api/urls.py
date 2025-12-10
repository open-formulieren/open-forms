from django.urls import path

from .views import CommunicationPreferencesView

app_name = "prefill_customer_interactions"


urlpatterns = [
    path(
        "communication-preferences/<uuid:submission_uuid>/component/<str:profile_component>",
        CommunicationPreferencesView.as_view(),
        name="communication-preferences",
    ),
]
