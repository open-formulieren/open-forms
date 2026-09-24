from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterator
from copy import deepcopy
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, override

from autoslug import AutoSlugField
from typing_extensions import deprecated

from formio_types import CustomerProfile, Email
from openforms.formio.service import dump_to_legacy
from openforms.formio.utils import iter_components
from openforms.utils.helpers import get_charfield_max_length, truncate_str_if_needed

from ..models import Form
from ..validators import validate_template_expressions

if TYPE_CHECKING:
    from openforms.formio.datastructures import FormioConfig

    from ..models import FormStep


def _get_number_of_components(form_definition: FormDefinition) -> int:
    """
    Given a form definition, count the total number of (nested) components in the configuration.
    """
    count = 0
    for __ in form_definition.formio_config:
        count += 1
    del form_definition.formio_config  # avoid stale caches in tests etc.
    return count


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
    slug = AutoSlugField(_("slug"), max_length=100, populate_from="name", editable=True)
    # TODO: this should ideally be a smarter field that exclusively communicates in
    # FormioConfig data structures
    configuration = models.JSONField(
        _("Form.io configuration"),
        help_text=_("The form definition as Form.io JSON schema"),
        validators=[validate_template_expressions],
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

    # de-normalized fields that cannot be easily computed on the fly in the DB
    _num_components = models.PositiveIntegerField(
        _("number of Formio components"),
        default=0,
        help_text=_("The total number of Formio components used in the configuration"),
    )

    formstep_set: models.Manager[FormStep]

    class Meta:
        verbose_name = _("Form definition")
        verbose_name_plural = _("Form definitions")

    def __str__(self):
        return self.admin_name

    def save(self, *args, **kwargs):
        # on every save, keep track of the number of components
        self._num_components = _get_number_of_components(self)

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if Form.objects.filter(formstep__form_definition=self).exists():
            raise ValidationError(
                _(
                    "This form definition cannot be removed because it is used in one or more forms."
                )
            )

        return super().delete(using=using, keep_parents=keep_parents)

    def clean(self):
        from ..validators import validate_form_definition_is_reusable

        super().clean()
        validate_form_definition_is_reusable(self)

    @transaction.atomic
    def copy(self):
        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = uuid.uuid4()
        copy.internal_name = (
            _("{name} (copy)").format(name=self.internal_name)
            if self.internal_name
            else ""
        )
        copy.slug = _("{slug}-copy").format(slug=self.slug)

        # truncate name and internal name if needed
        copy.internal_name = truncate_str_if_needed(
            self.internal_name,
            copy.internal_name,
            get_charfield_max_length(self, "internal_name"),
        )

        # name is handled by modeltranslation library and we want to make sure
        # it's translated for all the available languages
        language_codes = [item[0] for item in settings.LANGUAGES]
        for lang in language_codes:
            with override(lang):
                copy.name = _("{name} (copy)").format(name=self.name)

                # truncate name if needed
                copy.name = truncate_str_if_needed(
                    self.name, copy.name, get_charfield_max_length(self, "name")
                )

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
        if not self.pk:
            return Form.objects.none()
        return (
            Form.objects.filter(
                _is_deleted=False,
                formstep__form_definition=self,
            )
            .distinct()
            .order_by("name")
        )

    def get_hash(self):
        # normalize the configuration(s) with a msgspec/type conversion roundtrip
        normalized_components = dump_to_legacy(self.formio_config.components)
        return hashlib.md5(
            json.dumps(normalized_components, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @cached_property
    def formio_config(self) -> FormioConfig:
        from openforms.formio.datastructures import FormioConfig

        return FormioConfig(
            name=self.admin_name, components=self.configuration.get("components", [])
        )

    @deprecated("Deprecated in favour of formio_config datastructure")
    def iter_components(self, configuration=None, recursive=True, **kwargs):
        if configuration is None:
            configuration = self.configuration
        return iter_components(
            configuration=configuration, recursive=recursive, **kwargs
        )

    def get_keys_for_email_confirmation(self) -> Iterator[str]:
        """Return the key of fields to include in the confirmation email"""
        for component in self.formio_config:
            match component:
                case (
                    Email(confirmation_recipient=True)
                    | CustomerProfile(confirmation_recipient=True)
                ):
                    yield component.key

    @property
    def admin_name(self):
        return self.internal_name or self.name
