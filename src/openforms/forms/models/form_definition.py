import hashlib
import json
import uuid
from copy import deepcopy
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, override

from autoslug import AutoSlugField

from openforms.formio.utils import iter_components
from openforms.utils.helpers import get_charfield_max_length, truncate_str_if_needed

from ..models import Form
from ..validators import validate_template_expressions

if TYPE_CHECKING:
    from openforms.formio.service import FormioConfigurationWrapper


def _get_number_of_components(form_definition: "FormDefinition") -> int:
    """
    Given a form definition, count the total number of (nested) components in the configuration.
    """
    all_components = iter_components(form_definition.configuration, recursive=True)
    return len(list(all_components))


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
        return hashlib.md5(
            json.dumps(self.configuration, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @cached_property
    def configuration_wrapper(self) -> "FormioConfigurationWrapper":
        from openforms.formio.service import FormioConfigurationWrapper

        return FormioConfigurationWrapper(self.configuration)

    def iter_components(self, configuration=None, recursive=True, **kwargs):
        if configuration is None:
            configuration = self.configuration
        return iter_components(
            configuration=configuration, recursive=recursive, **kwargs
        )

    def get_keys_for_email_confirmation(self) -> list[tuple[str, str]]:
        """Return the key of fields to include in the confirmation email"""
        keys_for_email_confirmation = []

        for component in self.iter_components(recursive=True):
            if component.get("confirmationRecipient"):
                keys_for_email_confirmation.append(component["key"])

        return keys_for_email_confirmation

    @property
    def admin_name(self):
        return self.internal_name or self.name
