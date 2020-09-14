from django.db import models
from rest_framework.reverse import reverse


class Form(models.Model):
    """
    Form model, containing a list of order form steps.
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    active = models.BooleanField(default=False)
    product = models.ForeignKey(
        'core.Product',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    @property
    def login_required(self):
        return any([
            form_step.form_definition.login_required
            for form_step in self.formstep_set.all()
        ])

    @property
    def first_step(self):
        return self.formstep_set.first().order

    def get_api_form_steps(self, request):
        steps = [
            {
                'name': form_step.form_definition.name,
                'url': reverse(
                    'api:form-steps-detail',
                    kwargs={'form_slug': self.slug, 'slug': form_step.form_definition.slug},
                    request=request
                )
            } for form_step in self.formstep_set.all()
        ]

        return steps

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Form'
        verbose_name_plural = 'Forms'
