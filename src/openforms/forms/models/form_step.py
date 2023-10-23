import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from ordered_model.models import OrderedModel

from .utils import literal_getter


def populate_from_form_definition_name(instance: "FormStep"):
    existing_slug = instance.form_definition.slug
    return existing_slug or instance.form_definition.name


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
    slug = AutoSlugField(
        _("slug"),
        max_length=100,
        populate_from=populate_from_form_definition_name,
        editable=True,
        unique_with="form",
        null=True,
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
    is_applicable = models.BooleanField(
        _("is applicable"),
        default=True,
        help_text=_("Whether the step is applicable by default."),
    )

    order_with_respect_to = "form"

    get_previous_text = literal_getter("previous_text", "form_step_previous_text")
    get_save_text = literal_getter("save_text", "form_step_save_text")
    get_next_text = literal_getter("next_text", "form_step_next_text")

    form_id: int
    form_definition_id: int

    class Meta(OrderedModel.Meta):
        verbose_name = _("form step")
        verbose_name_plural = _("form steps")
        constraints = [
            models.UniqueConstraint(
                fields=["form", "form_definition"],
                name="form_form_definition_unique_together",
            ),
            models.UniqueConstraint(
                fields=["form", "slug"], name="form_slug_unique_together"
            ),
        ]

    def __str__(self):
        if self.form_id and self.form_definition_id:
            return _("{form_name} step {order}: {definition_name}").format(
                form_name=self.form.admin_name,
                order=self.order,
                definition_name=self.form_definition.admin_name,
            )
        else:
            return super().__str__()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        if self.form_definition.pk is not None and not self.form_definition.is_reusable:
            self.form_definition.delete()

    def iter_components(self, recursive=True, **kwargs):
        yield from self.form_definition.iter_components(recursive=recursive, **kwargs)

    def clean(self) -> None:
        if not self.is_applicable and self.order == 0:
            raise ValidationError(
                {"is_applicable": _("First form step must be applicable.")},
                code="invalid",
            )
        return super().clean()
