import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from ordered_model.models import OrderedModel
from rest_framework.reverse import reverse

from openforms.utils.fields import StringUUIDField

from ..constants import AvailabilityOptions


class FormStep(OrderedModel):
    """
    Through table for Form -> FormDefinitions.
    Allows for FormDefinitions to be reused as FormSteps in other Form instances.
    """

    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    form = models.ForeignKey("forms.Form", on_delete=models.CASCADE)
    form_definition = models.ForeignKey("forms.FormDefinition", on_delete=models.CASCADE)

    # step properties/flow control
    optional = models.BooleanField(
        _("optional"),
        default=False,
        help_text=_(
            "Designates whether this step is an optional step in the form. "
            "Currently used for form-rendering purposes, this is not (yet) used for "
            "validation purposes."
        ),
    )
    availability_strategy = models.CharField(
        _("availability"),
        max_length=50,
        choices=AvailabilityOptions,
        default=AvailabilityOptions.always,
        help_text=_(
            "Availability strategy to use. A step must be available before it can be "
            "filled out. Note that this is not validated (yet) during step submission."
        ),
    )

    order_with_respect_to = "form"

    class Meta:
        verbose_name = _("form step")
        verbose_name_plural = _("form steps")

    def __str__(self):
        return _("Form step {order}").format(order=self.order)

    def get_absolute_url(self):
        return reverse(
            "forms:form-steps-detail",
            kwargs={"slug": self.form.slug, "order": self.order},
        )
