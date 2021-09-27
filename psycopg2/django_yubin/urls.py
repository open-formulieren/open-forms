from django_yubin.views import MailHealthCheckView
from django.conf.urls import url


urlpatterns = [
    url(r'^health$', MailHealthCheckView.as_view(), name='yubin_health'),
]
