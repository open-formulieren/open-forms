import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from ordered_model.models import OrderedModel

from .utils import literal_getter


class FormStep(OrderedModel):
    """
    Through table for Form -> FormDefinitions.
    Allows for FormDefinitions to be reused as FormSteps in other Form instances.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    form = models.ForeignKey("forms.Form", on_delete=models.CASCADE)
    form_definition = models.ForeignKey(
        "forms.FormDefinition", on_delete=models.PROTECT
    )

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

    previous_text = models.CharField(
        _("step previous text"),
        max_length=50,
        blank=True,
        help_text=_(
            "The text that will be displayed in the form step to go to the previous step. "
            "Leave blank to get value from global configuration."
        ),
    )
    save_text = models.CharField(
        _("step save text"),
        max_length=50,
        blank=True,
        help_text=_(
            "The text that will be displayed in the form step to save the current information. "
            "Leave blank to get value from global configuration."
        ),
    )
    next_text = models.CharField(
        _("step next text"),
        max_length=50,
        blank=True,
        help_text=_(
            "The text that will be displayed in the form step to go to the next step. "
            "Leave blank to get value from global configuration."
        ),
    )

    order_with_respect_to = "form"

    get_previous_text = literal_getter("previous_text", "form_step_previous_text")
    get_save_text = literal_getter("save_text", "form_step_save_text")
    get_next_text = literal_getter("next_text", "form_step_next_text")

    class Meta(OrderedModel.Meta):
        verbose_name = _("form step")
        verbose_name_plural = _("form steps")

    def __str__(self):
        if self.form_id and self.form_definition_id:
            return _("{form_name} step {order}: {definition_name}").format(
                form_name=self.form.admin_name,
                order=self.order,
                definition_name=self.form_definition.admin_name,
            )
        else:
            return super().__str__()

    def iter_components(self, recursive=True):
        yield from self.form_definition.iter_components(recursive=recursive)
