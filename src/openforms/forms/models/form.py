import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from rest_framework.reverse import reverse

from openforms.registrations.fields import BackendChoiceField
from openforms.utils.fields import StringUUIDField


class Form(models.Model):
    """
    Form model, containing a list of order form steps.
    """

    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    slug = AutoSlugField(max_length=100, editable=True, unique=True)
    active = models.BooleanField(default=False)
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.CASCADE
    )

    # backend integration - which registration to use?
    registration_backend = BackendChoiceField(_("registration backend"), blank=True)
    registration_backend_options = JSONField(default=dict, blank=True, null=True)

    @property
    def login_required(self) -> bool:
        return any(
            [
                form_step.form_definition.login_required
                for form_step in self.formstep_set.all()
            ]
        )

    @property
    def first_step(self):
        return self.formstep_set.first().order

    def get_absolute_url(self):
        return reverse("forms:form-detail", kwargs={"slug": self.slug})

    def get_api_url(self):
        return reverse("api:form-detail", kwargs={"uuid": self.uuid})

    @transaction.atomic
    def copy(self):
        form_steps = self.formstep_set.all()
        self.pk = None
        self.uuid = uuid.uuid4()
        self.name = f"{self.name} (kopie)"
        self.product = None
        self.save()

        for form_step in form_steps:
            form_step.pk = None
            form_step.uuid = uuid.uuid4()
            form_step.form = self
            form_step.save()

        return self

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Form"
        verbose_name_plural = "Forms"
