from django.contrib.postgres.fields import JSONField
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.urls import reverse


class FormDefinition(models.Model):
    """
    Form Definition containing the form configuration that is created by the form builder,
    and used to render the form.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    configuration = JSONField()

    login_required = models.BooleanField(
        default=False,
        help_text="Geef aan of een DigID Login vereist is."
    )
    scheme_url = models.URLField(
        verbose_name=_("Schema URL"),
        help_text=_("Indien ingevuld word deze URL gebruikt voor de JSON representatie."),
        blank=True,
        null=True
    )

    def get_absolute_url(self):
        return reverse("core:form_definition_detail", kwargs={"slug": self.slug})

    def get_scheme_url(self):
        """
        TODO: Can this be reversed/made not hardcoded?
        """
        if self.scheme_url:
            return self.scheme_url

        return f"/api/v1/form-definitions/{self.slug}"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Formulier definitie")
        verbose_name_plural = _("Form definities")
