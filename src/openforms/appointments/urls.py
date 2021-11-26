from django.urls import path

from .views import VerifyCancelAppointmentLinkView, VerifyChangeAppointmentLinkView

app_name = "appointments"

urlpatterns = [
    path(
        "<uuid:submission_uuid>/<str:token>/verify-cancel",
        VerifyCancelAppointmentLinkView.as_view(),
        name="appointments-verify-cancel-appointment-link",
    ),
    path(
        "<uuid:submission_uuid>/<str:token>/verify-change",
        VerifyChangeAppointmentLinkView.as_view(),
        name="appointments-verify-change-appointment-link",
    ),
]
