import uuid

from django.db import models

from rest_framework.reverse import reverse

from openforms.utils.fields import StringUUIDField


class Form(models.Model):
    """
    Form model, containing a list of order form steps.
    """
    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    active = models.BooleanField(default=False)
    product = models.ForeignKey(
        'products.Product',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    backend = models.CharField(max_length=100, blank=True)

    @property
    def login_required(self):
        return any([
            form_step.form_definition.login_required
            for form_step in self.formstep_set.all()
        ])

    @property
    def first_step(self):
        return self.formstep_set.first().order

    def get_absolute_url(self):
        return reverse('core:form-detail', kwargs={'slug': self.slug})

    def get_api_url(self):
        return reverse('api:form-detail', kwargs={'uuid': self.uuid})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Form'
        verbose_name_plural = 'Forms'
