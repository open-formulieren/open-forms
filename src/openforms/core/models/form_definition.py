
from django.contrib.postgres.fields import JSONField
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
        help_text='DigID Login required for form step'
    )

    def get_absolute_url(self):
        return reverse("core:form_definition_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Form Definition"
        verbose_name_plural = "Form Definitions"
