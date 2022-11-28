from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

import jq
from rest_framework.serializers import ValidationError as DRFValidationError

from openforms.forms.api.validators import JsonLogicValidator

from .constants import DataMappingTypes, ServiceFetchMethods
from .validators import HeaderValidator


class ServiceFetchConfiguration(models.Model):
    service = models.ForeignKey(
        "zgw_consumers.Service",
        on_delete=models.PROTECT,
        verbose_name=_("service"),
    )
    path = models.CharField(
        _("path"),
        max_length=250,
        blank=True,  # allow "" for the root, but not None
        default="",
        help_text=_("path relative to the Service API root"),
    )
    method = models.CharField(
        _("HTTP method"),
        max_length=4,
        choices=ServiceFetchMethods.choices,
        default=ServiceFetchMethods.get,
        help_text=_("POST is allowed, but should not be used to mutate data"),
    )
    headers = models.JSONField(
        _("HTTP request headers"),
        blank=True,
        null=True,
        help_text=_(
            "Additions and overrides for the HTTP request headers as defined in the Service."
        ),
        validators=[HeaderValidator()],
    )
    query_params = models.TextField(
        _("HTTP query string"),
        blank=True,
        default="",
    )
    body = models.JSONField(
        _("HTTP request body"),
        blank=True,
        null=True,
        help_text=_(
            'Request body for POST requests (only "application/json" is supported)'
        ),
    )
    data_mapping_type = models.CharField(
        _("mapping expression language"),
        max_length=10,
        blank=True,
        default="",
        choices=DataMappingTypes.choices,
    )
    mapping_expression = models.JSONField(
        _("mapping expression"),
        blank=True,
        null=True,
        help_text=_("For jq, pass a string containing the filter expression"),
    )

    class Meta:
        verbose_name = _("service fetch configuration")
        verbose_name_plural = _("service fetch configurations")

    def __str__(self):
        return f"{self.service} {self.path}"

    def clean(self):
        super().clean()
        errors = {}

        if self.method == ServiceFetchMethods.get and self.body not in (None, ""):
            errors["body"] = _("GET requests may not have a body")

        if self.data_mapping_type == "" and self.mapping_expression not in (None, ""):
            errors["mapping_expression"] = _("Data mapping type missing for expression")
        elif self.data_mapping_type != "" and self.mapping_expression is None:
            errors["mapping_expression"] = _(
                "Missing {mapping_type} expression"
            ).format(mapping_type=self.data_mapping_type)
        elif self.data_mapping_type == DataMappingTypes.jq:
            try:
                jq.compile(self.mapping_expression)
            except ValueError as e:
                errors["mapping_expression"] = str(e)
        elif self.data_mapping_type == DataMappingTypes.json_logic:
            try:
                JsonLogicValidator()(self.mapping_expression)
            except (DRFValidationError, ValidationError) as e:
                errors["mapping_expression"] = str(e.__cause__)

        if errors:
            raise ValidationError(errors)
