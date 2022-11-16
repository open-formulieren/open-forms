from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

import jq
from json_logic import jsonLogic

from .constants import DataMappingTypes, ServiceFetchMethods


class ServiceFetchConfiguration(models.Model):
    service = models.ForeignKey(
        "zgw_consumers.Service",
        on_delete=models.PROTECT,
    )
    path = models.CharField(
        max_length=250,
        blank=True,  # allow "" for the root, but not None
        default="",
        help_text=_("path relative to the Service API root"),
    )
    method = models.CharField(
        max_length=4,
        choices=ServiceFetchMethods.choices,
        default="GET",
        help_text=_("POST is allowed, but should not be used to mutate data"),
    )
    headers = models.JSONField(
        blank=True,
        null=True,
        help_text=_(
            "Additions and overrides for the HTTP request headers as defined in the Service."
        ),
    )
    query_params = models.TextField(
        blank=True,
        default="",
    )
    body = models.JSONField(
        blank=True,
        null=True,
        help_text=_(
            'Request body for POST requests (only "application/json" is supported)'
        ),
    )
    data_mapping_type = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=DataMappingTypes.choices,
    )
    mapping_expression = models.JSONField(
        blank=True,
        null=True,
        help_text=_("For jq, pass a string containing the filter expression"),
    )

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        errors = {}

        if self.method == "GET" and self.body not in (None, ""):
            errors["body"] = _("GET requests may not have a body")

        if self.data_mapping_type is None and self.mapping_expression not in (None, ""):
            errors["mapping_expression"] = _("Data mapping type missing for expression")
        elif self.data_mapping_type == DataMappingTypes.jq:
            try:
                jq.compile(self.mapping_expression)
            except ValueError as e:
                errors["mapping_expression"] = str(e)
        elif self.data_mapping_type == DataMappingTypes.json_logic:
            try:
                jsonLogic(self.mapping_expression)
            except ValueError as e:
                errors["mapping_expression"] = str(e)

        if errors:
            raise ValidationError(errors)
