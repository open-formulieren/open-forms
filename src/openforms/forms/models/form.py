import uuid as _uuid
from copy import deepcopy
from typing import List

from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from rest_framework.reverse import reverse
from tinymce.models import HTMLField

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

    # backend integration - which registration to use?
    registration_backend = BackendChoiceField(_("registration backend"), blank=True)
    registration_backend_options = JSONField(
        _("registration backend options"), default=dict, blank=True, null=True
    )

    authentication_backends = BackendMultiSelectField(
        _("authentication backend(s)"),
        blank=True,
    )
    submission_confirmation_template = HTMLField(
        _("submission confirmation template"),
        help_text=_(
            "The content of the submission confirmation page. It can contain variables that will be "
            "templated from the submitted form data. If not specified, the global template will be used."
        ),
        blank=True,
    )

    show_progress_indicator = models.BooleanField(
        _("show progress indicator"),
        default=True,
        help_text=_(
            "Whether the step progression should be displayed in the UI or not."
        )
    )
    previous_text = models.CharField(
        _("Previous Text"),
        max_length=50,
        default=_("Previous page"),
        help_text=_(
            "The text that will be displayed in the overview page to go to the previous step"
        ),
    )
    change_text = models.CharField(
        _("Change Text"),
        max_length=50,
        default=_("Change"),
        help_text=_(
            "The text that will be displayed in the overview page to change a certain step"
        ),
    )
    confirm_text = models.CharField(
        _("Confirm Text"),
        max_length=50,
        default=_("Confirm"),
        help_text=_(
            "The text that will be displayed in the overview page to confirm the data is correct"
        ),
    )

    # life cycle management
    active = models.BooleanField(default=False)
    maintenance_mode = models.BooleanField(
        _("maintenance mode"),
        default=False,
        help_text=_(
            "Users will not be able to start the form if it is in maintenance mode."
        ),
    )
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

    def get_keys_for_email_confirmation(self) -> List[str]:
        return_keys = set()
        for form_step in self.formstep_set.select_related("form_definition"):
            for key in form_step.form_definition.get_keys_for_email_confirmation():
                if key:
                    return_keys.add(key)
        return list(return_keys)
