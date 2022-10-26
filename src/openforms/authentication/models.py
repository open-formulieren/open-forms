from django.contrib.auth.hashers import make_password as get_salted_hash
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.contrib.kvk.validators import validate_kvk
from openforms.utils.validators import validate_bsn

from .constants import AuthAttribute
from .tasks import hash_identifying_attributes as hash_identifying_attributes_task


class BaseAuthInfo(models.Model):
    plugin = models.CharField(
        verbose_name=_("plugin"),
        help_text=_("Identifier of the authentication plugin."),
        max_length=250,
    )
    attribute = models.CharField(
        verbose_name=_("attribute"),
        help_text=_("Name of the attribute returned by the authentication plugin."),
        choices=AuthAttribute.choices,
        max_length=50,
    )
    value = models.CharField(
        verbose_name=_("value"),
        help_text=_("Value of the attribute returned by the authentication plugin."),
        max_length=250,
    )
    attribute_hashed = models.BooleanField(
        verbose_name=_("identifying attributes hashed"),
        help_text=_("Are the auth/identifying attributes hashed?"),
        default=False,
    )

    class Meta:
        abstract = True
        verbose_name = _("Authentication details")
        verbose_name_plural = _("Authentication details")

    def clear_sensitive_data(self):
        self.value = ""
        self.save()

    def hash_identifying_attributes(self, delay=False):
        """
        Generate a salted hash for each of the identifying attributes.

        Hashes allow us to compare correct values at a later stage, while still
        preventing sensitive data to be available in plain text if the database were
        to leak.

        We use :mod:`django.contrib.auth.hashers` for the actual salting and hashing,
        relying on the global Django ``PASSWORD_HASHERS`` setting.
        """
        if delay:
            hash_identifying_attributes_task.delay(self.pk)
            return

        self.value = get_salted_hash(self.value)
        self.attribute_hashed = True
        self.save()

    def clean(self):
        if self.attribute == AuthAttribute.bsn:
            validate_bsn(self.value)
        elif self.attribute == AuthAttribute.kvk:
            validate_kvk(self.value)


# TODO: what about co-sign data?
class AuthInfo(BaseAuthInfo):
    submission = models.OneToOneField(
        to="submissions.Submission",
        verbose_name=_("Submission"),
        on_delete=models.CASCADE,
        help_text=_("Submission related to this authentication information"),
        related_name="auth_info",
    )
    machtigen = models.JSONField(
        verbose_name=_("machtigen"),
        help_text=_(
            "Data related to any 'machtiging' (authorising someone else to perform actions on your behalf)."
        ),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Authentication details")
        verbose_name_plural = _("Authentication details")


class RegistratorInfo(BaseAuthInfo):
    submission = models.OneToOneField(
        to="submissions.Submission",
        verbose_name=_("Submission"),
        on_delete=models.CASCADE,
        help_text=_("Submission related to this authentication information"),
        related_name="_registrator",
    )

    class Meta:
        verbose_name = _("Registrator authentication details")
        verbose_name_plural = _("Registrator authentication details")

        permissions = [
            (
                "can_register_customer_submission",
                _("Can register submission for customers"),
            ),
        ]
