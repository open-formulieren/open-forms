from django.urls import path
from django.views.generic import TemplateView, RedirectView

app_name = 'sample_app'

urlpatterns = [
    path('digid-login', TemplateView.as_view(template_name='sample_app/views/digid_login/digid_login.html'), name='digid_login'),
    path('form-details', TemplateView.as_view(template_name='sample_app/views/form_details/form_details.html'), name='form_details'),
    path('', RedirectView.as_view(url="form-details")),

]
