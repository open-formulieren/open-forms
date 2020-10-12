import uuid

from django.db import models
from rest_framework.reverse import reverse

from ordered_model.models import OrderedModel
from rest_framework.reverse import reverse

from openforms.utils.fields import StringUUIDField


class FormStep(OrderedModel):
    """
    Through table for Form -> FormDefinitions.
    Allows for FormDefinitions to be reused as FormSteps in other Form instances.
    """
    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    form = models.ForeignKey('core.Form', on_delete=models.CASCADE)
    form_definition = models.ForeignKey('core.FormDefinition', on_delete=models.CASCADE)
    order_with_respect_to = 'form'

    def get_api_url(self):
        return reverse(
            'api:form-steps-detail',
            kwargs={'form_uuid': self.form.uuid, 'uuid': self.uuid},
        )

    def __str__(self):
        return f'Form Step {str(self.order)}'

    def get_absolute_url(self):
        return reverse('core:form-steps-detail', kwargs={'slug': self.form.slug, 'order': self.order})

    def get_api_url(self, request):
        return reverse('api:form-steps-detail', kwargs={'form_slug': self.form.slug, 'order': self.order}, request=request)

    class Meta:
        verbose_name = 'Form Step'
        verbose_name_plural = 'Form Steps'
