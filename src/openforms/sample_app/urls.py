from django.urls import path
from django.views.generic import TemplateView, RedirectView, ListView, DetailView

from openforms.core.models import FormDefinition

app_name = 'sample_app'

urlpatterns = [
    path('prototype/digid-login', TemplateView.as_view(template_name='sample_app/views/prototype/digid_login/digid_login.html'), name='digid_login'),

    path('prototype/form-details', TemplateView.as_view(template_name='sample_app/views/prototype/form_details/form_details.html'), name='form_details'),
    path('prototype/orm-details/errors', TemplateView.as_view(template_name='sample_app/views/prototype/form_details/form_details_errors.html'), name='form_details_errors'),

    path('prototype/form-appointment', TemplateView.as_view(template_name='sample_app/views/prototype/form_appointment/form_appointment.html'), name='form_appointment'),
    path('prototype/form-appointment/errors', TemplateView.as_view(template_name='sample_app/views/prototype/form_appointment/form_appointment_errors.html'), name='form_appointment_errors'),

    path('prototype/form-contact', TemplateView.as_view(template_name='sample_app/views/prototype/form_contact/form_contact.html'), name='form_contact'),
    path('prototype/form-contact/errors', TemplateView.as_view(template_name='sample_app/views/prototype/form_contact/form_contact_errors.html'), name='form_contact_errors'),

    path('prototype/overview', TemplateView.as_view(template_name='sample_app/views/prototype/overview/overview.html'), name='overview'),

    path('vanilla/<slug:slug>', DetailView.as_view(model=FormDefinition, template_name='sample_app/views/vanilla/vanilla_detail.html')),

    path('', RedirectView.as_view(url="/prototype/digid-login")),

]
