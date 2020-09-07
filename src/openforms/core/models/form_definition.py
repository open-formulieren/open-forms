
from django.contrib.postgres.fields import JSONField
from django.db import models


class FormDefinition(models.Model):
    """
    Form Definition containing the form configuration that is created by the form builder,
    and used to render the form.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    configuration = JSONField()
    product = models.ForeignKey(
        'core.Product',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Form Definition"
        verbose_name_plural = "Form Definitions"
