from collections.abc import Collection

from django.contrib.auth.hashers import make_password as get_salted_hash
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from openforms.contrib.kvk.validators import validate_kvk
from openforms.utils.validators import validate_bsn

from .constants import (
    ActingSubjectIdentifierType,
    AuthAttribute,
    LegalSubjectIdentifierType,
)
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
        if self.attribute == AuthAttribute.bsn and not self.attribute_hashed:
            validate_bsn(self.value)
        elif self.attribute == AuthAttribute.kvk and not self.attribute_hashed:
            validate_kvk(self.value)


class ConjointConstraint(models.CheckConstraint):
    """
    The provided (string) fields must all or none have a non-empty value.
    """

    def __init__(
        self, *, fields: Collection[str], name: str, violation_error_message=None
    ):
        self.fields = fields
        check = self._build_check(fields)
        super().__init__(
            name=name, check=check, violation_error_message=violation_error_message
        )

    def _build_check(self, fields: Collection[str]):
        # This is the opposite of mutual exclusivity
        all_empty = [Q(**{f"{field}__exact": ""}) for field in fields]
        none_empty = [~q for q in all_empty]
        return Q(*all_empty) | Q(*none_empty)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs.pop("check")
        kwargs["fields"] = self.fields
        return path, args, kwargs


# TODO: what about co-sign data?
class AuthInfo(BaseAuthInfo):
    # Relation to submission - there can only be a single auth info for a submission.
    submission = models.OneToOneField(
        to="submissions.Submission",
        verbose_name=_("Submission"),
        on_delete=models.CASCADE,
        help_text=_("Submission related to this authentication information"),
        related_name="auth_info",
    )

    # authentication details of the representee (without mandate/machtigen, this is the
    # logged in actor themselves) are stored in the fields `plugin`, `attribute` and `value`.
    # They match the (inferred) `representee.identifierType` and
    # `representee.identifier`.

    # together with the value of `plugin`, this tracks the way authentication was
    # performed.
    loa = models.TextField(
        verbose_name=_("Level of assurance"),
        help_text=_(
            "How certain is the identity provider that this identity belongs to this user."
        ),
        default="",  # not all plugins support this concept
        blank=True,
    )

    # track information about the mandate/machtigen. Note that this also captures an
    # employee authenticating for their company, they are then the acting subject and
    # the company is the legal subject.
    acting_subject_identifier_type = models.CharField(
        verbose_name=_("acting subject identifier type"),
        help_text=_(
            "The identifier type determines how to interpret the identifier value."
        ),
        max_length=50,
        blank=True,
        choices=ActingSubjectIdentifierType.choices,
    )
    acting_subject_identifier_value = models.CharField(
        verbose_name=_("acting subject identifier"),
        help_text=_("(Contextually) unique identifier for the acting subject."),
        max_length=250,
        blank=True,
    )

    legal_subject_identifier_type = models.CharField(
        verbose_name=_("legal subject identifier type"),
        help_text=_(
            "The identifier type determines how to interpret the identifier value."
        ),
        max_length=50,
        blank=True,
        choices=LegalSubjectIdentifierType.choices,
    )
    legal_subject_identifier_value = models.CharField(
        verbose_name=_("legal subject identifier"),
        help_text=_("(Contextually) unique identifier for the legal subject."),
        max_length=250,
        blank=True,
    )

    mandate_context = models.JSONField(
        verbose_name=_("mandate context"),
        help_text=_(
            "If a mandate is in play, then the mandate context must be provided. The "
            "details are tracked here, in line with the authentication context data "
            "JSON schema definition."
        ),
        blank=True,
        null=True,
    )

    # deprecated!
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
        constraints = [
            # if a type or value for action/legal subject is given, then the other
            # property must be provided too.
            ConjointConstraint(
                name="acting_subject_integrity",
                fields=(
                    "acting_subject_identifier_type",
                    "acting_subject_identifier_value",
                ),
            ),
            ConjointConstraint(
                name="legal_subject_integrity",
                fields=(
                    "legal_subject_identifier_type",
                    "legal_subject_identifier_value",
                ),
            ),
            # presence of a legal subject implies a mandata context
            models.CheckConstraint(
                name="mandate_context_not_null",
                check=(
                    Q(legal_subject_identifier_value="", mandate_context__isnull=True)
                    | Q(
                        ~Q(legal_subject_identifier_value=""),
                        mandate_context__isnull=False,
                    )
                ),
            ),
            # TODO: add constraints matching the json schema for the identifier types
        ]


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
