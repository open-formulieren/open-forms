
from django.contrib.postgres.fields import JSONField
from django.db import models
from rest_framework.reverse import reverse


class FormDefinition(models.Model):
    """
    Form Definition containing the form configuration that is created by the form builder,
    and used to render the form.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    configuration = JSONField()
    active = models.BooleanField(default=False)
    product = models.ForeignKey(
        'core.Product',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    def get_config_api_url(self, request):
        return reverse('api:configurations', args=(self.slug,), request=request)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Form Definition"
        verbose_name_plural = "Form Definitions"
