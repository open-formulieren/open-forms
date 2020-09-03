from django.urls import path
from django.views.generic import TemplateView, RedirectView

app_name = 'sample_app'

urlpatterns = [
    path('digid-login', TemplateView.as_view(template_name='sample_app/views/digid_login/digid_login.html'), name='digid-login'),
    path('', RedirectView.as_view(url="digid-login")),

]
