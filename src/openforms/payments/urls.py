from django.urls import path

from .contrib.ogone.views import DevView
from .views import PaymentReturnView, PaymentStartView, PaymentWebhookiew

app_name = "payments"

urlpatterns = [
    path(
        # TODO remove before merge
        "dev",
        DevView.as_view(),
        name="dev",
    ),
    path(
        "<uuid:uuid>/<slug:plugin_id>/start",
        PaymentStartView.as_view(),
        name="start",
    ),
    path(
        "<uuid:uuid>/<slug:plugin_id>/return",
        PaymentReturnView.as_view(),
        name="return",
    ),
    path(
        "<uuid:uuid>/<slug:plugin_id>/webhook",
        PaymentWebhookiew.as_view(),
        name="webhook",
    ),
]
