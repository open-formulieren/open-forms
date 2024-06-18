from django.urls import path

from mozilla_django_oidc_db.views import OIDCCallbackView

# XXX: sort out callback endpoints
# deprecated
urlpatterns = [
    path("callback/", OIDCCallbackView.as_view(), name="org-oidc-callback"),
]
