from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..constants import (
    FormVariablesDataTypes,
    FormVariablesInitialValues,
    FormVariablesSources,
)
from .form import Form
from .form_definition import FormDefinition


def get_today():
    return timezone.now().isoformat()


STATIC_INITIAL_VALUES = {FormVariablesInitialValues.today: get_today}


class FormVariable(models.Model):
    form = models.ForeignKey(
        to=Form,
        verbose_name=_("form"),
        help_text=_("Form to which this variable is related"),
        on_delete=models.CASCADE,
    )
    form_definition = models.ForeignKey(
        to=FormDefinition,
        verbose_name=_("form definition"),
        help_text=_(
            "Form definition to which this variable is related. This is kept as metadata"
        ),
        on_delete=models.CASCADE,
        null=True,
    )
    name = models.CharField(
        verbose_name=_("name"),
        help_text=_("Name of the variable"),
        max_length=100,
    )
    slug = models.SlugField(
        verbose_name=_("slug"),
        help_text=_("Slug name of the variable, should be unique per form."),
    )
    source = models.CharField(
        verbose_name=_("source"),
        help_text=_(
            "Where will the data that will be associate with this variable come from"
        ),
        choices=FormVariablesSources.choices,
        max_length=50,
    )
    prefill_plugin = models.CharField(
        verbose_name=_("prefill plugin"),
        help_text=_("Which, if any, prefill plugin should be used"),
        blank=True,
        max_length=50,
    )
    prefill_attribute = models.CharField(
        verbose_name=_("prefill attribute"),
        help_text=_(
            "Which attribute from the prefill response should be used to fill this variable"
        ),
        blank=True,
        max_length=50,
    )
    data_type = models.CharField(
        verbose_name=_("data type"),
        help_text=_("The type of the value that will be associated with this variable"),
        choices=FormVariablesDataTypes.choices,
        max_length=50,
    )
    data_format = models.CharField(
        verbose_name=_("data format"),
        help_text=_(
            "The format of the value that will be associated with this variable"
        ),
        blank=True,
        max_length=250,
    )
    is_sensitive_data = models.BooleanField(
        verbose_name=_("is sensitive data"),
        help_text=_("Will this variable be associated with sensitive data?"),
        default=True,
    )
    initial_value = models.JSONField(
        verbose_name=_("initial value"),
        help_text=_("The initial value for this field"),
    )

    class Meta:
        verbose_name = _("Form variable")
        verbose_name_plural = _("Form variables")
        unique_together = ("slug", "form")

    def __str__(self):
        return _("Form variable %(name)s") % {"name": self.name}

    def get_initial_value(self):
        if self.source == FormVariablesSources.static:
            return STATIC_INITIAL_VALUES[self.initial_value]()
        else:
            return self.initial_value
