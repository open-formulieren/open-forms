from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext, gettext_lazy as _


def generate_verification_code():
    """
    Generate a 6-character verification code.

    The code is not required to be globally unique, so it's okay if the same code is
    generated for different email addresses.
    """
    return get_random_string(length=6, allowed_chars="0123456789")


class CosignOTP(models.Model):
    """
    One-time password for cosign flows.
    """

    submission = models.ForeignKey(
        "Submission",
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
    )
    verification_code = models.CharField(
        _("verification code"),
        max_length=6,
        default=generate_verification_code,
    )
    expires_at = models.DateTimeField(
        _("expiry date"),
        null=False,
        blank=False,
        help_text=_("Timestamp when the one-time password expires."),
    )

    class Meta:
        verbose_name = _("Cosign one-time password")
        verbose_name_plural = _("Cosign one-time passwords")

    def __str__(self):
        reference = (
            self.submission.public_registration_reference if self.submission else "-"
        )
        expired = gettext("(expired)") if self.is_expired else ""
        return (
            gettext("Submission {reference} {expired}")
            .format(reference=reference, expired=expired)
            .strip()
        )

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()
