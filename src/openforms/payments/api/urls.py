from django.urls import path

from .views import PaymentPluginListView

urlpatterns = [
    path("plugins", PaymentPluginListView.as_view(), name="payment-plugin-list"),
]
