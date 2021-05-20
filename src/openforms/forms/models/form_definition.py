import uuid
from copy import deepcopy
from typing import List

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField

from openforms.forms.models import Form
from openforms.utils.fields import StringUUIDField


class FormDefinition(models.Model):
    """
    Form Definition containing the form configuration that is created by the form builder,
    and used to render the form.
    """

    uuid = StringUUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    name = models.CharField(_("name"), max_length=50)
    slug = AutoSlugField(
        _("slug"), max_length=100, populate_from="name", editable=True, unique=True
    )
    configuration = JSONField(
        _("Formio.js configuration"),
        help_text=_("The form definition as Formio.js JSON schema"),
    )
    login_required = models.BooleanField(
        _("login required"),
        default=False,
        help_text="DigID Login required for form step",
    )

    def get_absolute_url(self):
        return reverse("forms:form_definition_detail", kwargs={"slug": self.slug})

    @transaction.atomic
    def copy(self):
        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = uuid.uuid4()
        copy.name = _("{name} (copy)").format(name=self.name)
        copy.slug = _("{slug}-copy").format(slug=self.slug)
        copy.save()
        return copy

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        if Form.objects.filter(formstep__form_definition=self).exists():
            raise ValidationError(
                _(
                    "This form definition cannot be removed because it is used in one or more forms."
                )
            )

        return super().delete(using=using, keep_parents=keep_parents)

    def get_keys_for_email_summary(self) -> List[str]:
        keys_for_email_summary = []
        components = self.configuration.get("configuration", {}).get("components")
        if components:
            for component in components:
                if component.get("showInEmail"):
                    keys_for_email_summary.append(component["key"])
        return keys_for_email_summary

    class Meta:
        verbose_name = _("Form definition")
        verbose_name_plural = _("Form definitions")
