from django.urls import path
from django.views.generic import RedirectView, TemplateView


app_name = 'sample_app'

urlpatterns = [
    path('digid-login', TemplateView.as_view(template_name='sample_app/views/prototype/digid_login/digid_login.html'), name='digid_login'),

    path('form-details', TemplateView.as_view(template_name='sample_app/views/prototype/form_details/form_details.html'), name='form_details'),
    path('form-details/errors', TemplateView.as_view(template_name='sample_app/views/prototype/form_details/form_details_errors.html'), name='form_details_errors'),

    path('form-appointment', TemplateView.as_view(template_name='sample_app/views/prototype/form_appointment/form_appointment.html'), name='form_appointment'),
    path('form-appointment/errors', TemplateView.as_view(template_name='sample_app/views/prototype/form_appointment/form_appointment_errors.html'), name='form_appointment_errors'),

    path('form-contact', TemplateView.as_view(template_name='sample_app/views/prototype/form_contact/form_contact.html'), name='form_contact'),
    path('form-contact/errors', TemplateView.as_view(template_name='sample_app/views/prototype/form_contact/form_contact_errors.html'), name='form_contact_errors'),

    path('overview', TemplateView.as_view(template_name='sample_app/views/prototype/overview/overview.html'), name='overview'),

    path('', RedirectView.as_view(url="/prototype/digid-login")),

]
