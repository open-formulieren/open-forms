import hashlib
import json
import uuid
from copy import deepcopy
from functools import partial
from typing import List, Tuple

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField

from ..models import Form
from ..tasks import detect_formiojs_configuration_snake_case


class FormDefinition(models.Model):
    """
    Form Definition containing the form configuration that is created by the form builder,
    and used to render the form.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    name = models.CharField(_("name"), max_length=50)
    internal_name = models.CharField(
        _("internal name"),
        blank=True,
        max_length=50,
        help_text=_("internal name for management purposes"),
    )
    slug = AutoSlugField(
        _("slug"), max_length=100, populate_from="name", editable=True, unique=True
    )
    configuration = JSONField(
        _("Form.io configuration"),
        help_text=_("The form definition as Form.io JSON schema"),
    )
    login_required = models.BooleanField(
        _("login required"),
        default=False,
        help_text="DigID Login required for form step",
    )
    is_reusable = models.BooleanField(
        _("is reusable"),
        default=False,
        help_text="Allow this definition to be re-used in multiple forms",
    )

    def __str__(self):
        return self.admin_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self._check_configuration_integrity()

    def get_absolute_url(self):
        return reverse("forms:form_definition_detail", kwargs={"slug": self.slug})

    def _check_configuration_integrity(self):
        if settings.DEBUG:
            callback = partial(
                detect_formiojs_configuration_snake_case, self.id, raise_exception=True
            )
        else:
            callback = partial(detect_formiojs_configuration_snake_case.delay, self.id)
        transaction.on_commit(callback)

    @transaction.atomic
    def copy(self):
        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = uuid.uuid4()
        copy.name = _("{name} (copy)").format(name=self.name)
        copy.internal_name = (
            _("{name} (copy)").format(name=self.internal_name)
            if self.internal_name
            else ""
        )
        copy.slug = _("{slug}-copy").format(slug=self.slug)
        copy.save()
        return copy

    @property
    def used_in(self) -> models.QuerySet:
        """
        Query the forms that make use of this definition.

        (Soft) deleted forms are excluded from this. This property is not intended
        to be used in bulk Form Definition querysets, you should use prefetch queries
        for that.
        """
        return (
            Form.objects.filter(
                _is_deleted=False,
                formstep__form_definition=self,
            )
            .distinct()
            .order_by("name")
        )

    def get_hash(self):
        return hashlib.md5(
            json.dumps(self.configuration, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def delete(self, using=None, keep_parents=False):
        if Form.objects.filter(formstep__form_definition=self).exists():
            raise ValidationError(
                _(
                    "This form definition cannot be removed because it is used in one or more forms."
                )
            )

        return super().delete(using=using, keep_parents=keep_parents)

    def iter_components(self, configuration=None, recursive=True):
        if configuration is None:
            configuration = self.configuration

        components = configuration.get("components")
        if configuration.get("type") == "columns" and recursive:
            assert not components, "Both nested components and columns found"
            for column in configuration["columns"]:
                yield from self.iter_components(
                    configuration=column, recursive=recursive
                )

        if components:
            for component in components:
                yield component
                if recursive:
                    yield from self.iter_components(
                        configuration=component, recursive=recursive
                    )

    def get_keys_for_email_summary(self) -> List[Tuple[str, str]]:
        """Return the key and the label of fields to include in the email summary"""
        keys_for_email_summary = []

        for component in self.iter_components(recursive=True):
            if component.get("showInEmail"):
                keys_for_email_summary.append((component["key"], component["label"]))

        return keys_for_email_summary

    def get_keys_for_email_confirmation(self) -> List[Tuple[str, str]]:
        """Return the key and the label of fields to include in the confirmation email"""
        keys_for_email_confirmation = []

        for component in self.iter_components(recursive=True):
            if component.get("confirmationRecipient"):
                keys_for_email_confirmation.append(component["key"])

        return keys_for_email_confirmation

    @cached_property
    def sensitive_fields(self):
        sensitive_fields = []

        for component in self.iter_components(recursive=True):
            if component.get("isSensitiveData"):
                sensitive_fields.append(component["key"])

        return sensitive_fields

    @property
    def admin_name(self):
        return self.internal_name or self.name

    class Meta:
        verbose_name = _("Form definition")
        verbose_name_plural = _("Form definitions")
