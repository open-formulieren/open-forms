from django.db import models

from ordered_model.models import OrderedModel


class FormStep(OrderedModel):
    """
    Through table for Form -> FormDefinitions.
    Allows for FormDefinitions to be reused as FormSteps in other Form instances.
    """
    form = models.ForeignKey('core.Form', on_delete=models.CASCADE)
    form_definition = models.ForeignKey('core.FormDefinition', on_delete=models.CASCADE)
    order_with_respect_to = 'form'

    def __str__(self):
        return f'Form Step {str(self.order)}'

    class Meta:
        verbose_name = 'Form Step'
        verbose_name_plural = 'Form Steps'
