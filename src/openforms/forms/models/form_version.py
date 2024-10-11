import uuid as _uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils.formats import localize
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from .form import Form

User = get_user_model()


class FormVersionManager(models.Manager):
    def create_for(
        self, form: Form, description="", user: AbstractBaseUser | None = None
    ) -> "FormVersion":
        """
        Create a new ``FormVersion`` record for a given form.
        """
        # circular dependencies
        from ..utils import form_to_json

        form_json = form_to_json(form.id)
        if not description:
            version_number = self.filter(form=form).count() + 1
            description = _("Version {number}").format(number=version_number)
        return self.create(
            form=form, export_blob=form_json, user=user, description=description
        )


def get_app_release():
    return settings.RELEASE or ""


def get_app_git_sha():
    return settings.GIT_SHA or ""


class FormVersion(models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    form = models.ForeignKey(
        verbose_name=_("form"),
        to="forms.Form",
        on_delete=models.CASCADE,
    )
    export_blob = models.JSONField(
        help_text=_(
            "The form, form definitions and form steps that make up this version, saved as JSON data."
        ),
    )
    created = models.DateTimeField(
        verbose_name=_("created"),
        help_text=_("Date and time of creation of the form version."),
        auto_now_add=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("user"),
        help_text=_("User who authored this version."),
    )
    description = models.TextField(
        _("version description"),
        blank=True,
        help_text=_("Description/context about this particular version."),
    )
    app_release = models.CharField(
        _("application version"),
        max_length=50,
        blank=True,
        help_text=_("App release/version at the time this version was created."),
        editable=False,
        default=get_app_release,
    )
    app_git_sha = models.CharField(
        _("application commit hash"),
        max_length=50,
        blank=True,
        help_text=_("Application commit hash at the time this version was created."),
        editable=False,
        default=get_app_git_sha,
    )

    objects = FormVersionManager()

    class Meta:
        verbose_name = _("form version")
        verbose_name_plural = _("form versions")

    def __str__(self):
        timestamp = localize(localtime(self.created))
        return f"{self.form.admin_name} ({timestamp})"
