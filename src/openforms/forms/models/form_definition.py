import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.utils.fields import StringUUIDField


class FormDefinition(models.Model):
    """
    Form Definition containing the form configuration that is created by the form builder,
    and used to render the form.
    """

    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    configuration = JSONField(
        _("Formio.js configuration"),
        help_text=_("The form definition as Formio.js JSON schema"),
    )
    login_required = models.BooleanField(
        default=False, help_text="DigID Login required for form step"
    )

    def get_absolute_url(self):
        return reverse("forms:form_definition_detail", kwargs={"slug": self.slug})

    def _get_kopie_name(self):
        if self.name.endswith('Kopie'):
            name = f'{self.name} 1'
        elif self.name[:-2].endswith('Kopie') and self.name[-1].isdigit():
            num = int(self.name[-1]) + 1
            name = f'{self.name[:-2]} {num}'
        else:
            name = f'{self.name} Kopie'
        return name

    def _get_slug_name(self):
        if self.slug.endswith('-kopie'):
            slug = f'{self.slug}1'
        elif self.slug[:-1].endswith('-kopie') and self.slug[-1].isdigit():
            num = int(self.slug[-1]) + 1
            slug = f'{self.slug[:-1]}{num}'
        else:
            slug = f'{self.slug}-kopie'
        return slug

    def copy(self):
        self.pk = None
        self.uuid = uuid.uuid4()
        self.name = self._get_kopie_name()
        self.slug = self._get_slug_name()
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Form Definition"
        verbose_name_plural = "Form Definitions"
