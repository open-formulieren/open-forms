import uuid
from copy import deepcopy

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

    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    slug = AutoSlugField(
        max_length=100, populate_from="name", editable=True, unique=True
    )
    configuration = JSONField(
        _("Formio.js configuration"),
        help_text=_("The form definition as Formio.js JSON schema"),
    )
    login_required = models.BooleanField(
        default=False, help_text="DigID Login required for form step"
    )

    def get_absolute_url(self):
        return reverse("forms:form_definition_detail", kwargs={"slug": self.slug})

    @transaction.atomic
    def copy(self):
        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = uuid.uuid4()
        copy.name = f"{self.name} (kopie)"
        copy.slug = f"{self.slug}-kopie"
        copy.save()
        return copy

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        if Form.objects.filter(formstep__form_definition=self).exists():
            raise ValidationError(
                _(
                    "Deze Form Definitie is bij een Form gebruikt en daarvoor mag niet wiegeren worden"
                )
            )

        return super().delete(using=using, keep_parents=keep_parents)

    class Meta:
        verbose_name = "Form Definition"
        verbose_name_plural = "Form Definitions"
