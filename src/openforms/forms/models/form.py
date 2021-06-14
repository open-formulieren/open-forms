import uuid as _uuid
from copy import deepcopy
from typing import List, Optional

from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from rest_framework.reverse import reverse

from openforms.authentication.fields import BackendMultiSelectField
from openforms.registrations.fields import BackendChoiceField
from openforms.utils.fields import StringUUIDField


class FormQuerySet(models.QuerySet):
    def live(self):
        return self.filter(active=True, _is_deleted=False)


class FormManager(models.Manager.from_queryset(FormQuerySet)):
    pass


class Form(models.Model):
    """
    Form model, containing a list of order form steps.
    """

    uuid = StringUUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    name = models.CharField(_("name"), max_length=50)
    slug = AutoSlugField(
        _("slug"), max_length=100, populate_from="name", editable=True, unique=True
    )
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.CASCADE
    )
    # TODO: add validator that this field is present in the form step form definition(s)
    email_property_name = models.CharField(
        _("email fieldname"),
        max_length=200,
        blank=True,
        help_text=_(
            "The name of the attribute in the submission data that contains the "
            "email address to which the confirmation email will be sent. "
            "If not specified, `email` will be used."
        ),
    )

    # backend integration - which registration to use?
    registration_backend = BackendChoiceField(_("registration backend"), blank=True)
    registration_backend_options = JSONField(
        _("registration backend options"), default=dict, blank=True, null=True
    )

    authentication_backends = BackendMultiSelectField(
        _("authentication backend(s)"),
        blank=True,
    )

    # life cycle management
    active = models.BooleanField(default=False)
    _is_deleted = models.BooleanField(default=False)

    objects = FormManager()

    class Meta:
        verbose_name = _("form")
        verbose_name_plural = _("forms")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("forms:form-detail", kwargs={"slug": self.slug})

    def get_api_url(self):
        return reverse("api:form-detail", kwargs={"uuid": self.uuid})

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

    @transaction.atomic
    def copy(self):
        form_steps = self.formstep_set.all()

        copy = deepcopy(self)
        copy.pk = None
        copy.uuid = _uuid.uuid4()
        copy.name = _("{name} (copy)").format(name=self.name)
        copy.slug = _("{slug}-copy").format(slug=self.slug)
        copy.product = None
        copy.save()

        for form_step in form_steps:
            form_step.pk = None
            form_step.uuid = _uuid.uuid4()
            form_step.form = copy
            form_step.save()

        return copy

    def get_email_recipients(self, submitted_data: dict) -> Optional[List[str]]:
        property_name = self.email_property_name or "email"
        emails = submitted_data.get(property_name)
        if isinstance(emails, str):
            return [emails]
        return emails
