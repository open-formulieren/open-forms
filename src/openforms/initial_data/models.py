import uuid as _uuid
from collections.abc import Callable
from datetime import datetime, timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.accounts.models import User
from openforms.forms.models import Form
from openforms.utils.validators import AllowedRedirectValidator

from .constants import SupportedAuthAttributes


class InitialSubmissionData(models.Model):
    """
    Store initial submission information for a particular form.
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    form = models.ForeignKey[Form](Form, on_delete=models.CASCADE)
    form_url = models.URLField(
        _("custom form url"),
        blank=True,
        max_length=1000,
        help_text=_(
            "URL where the form is embedded when this is different from Open Forms "
            "itself. If left blank, then the redirect URL will use Open Forms' own "
            "form detail page."
        ),
        validators=[AllowedRedirectValidator()],
    )
    representee_auth_attribute = models.CharField(
        _("representee auth attribute"),
        help_text=_(
            "Attribute that will be provided for the submission authentication."
        ),
        choices=SupportedAuthAttributes.choices,
        max_length=50,
    )
    # TODO: encryption of the value would be nice
    representee_auth_value = models.CharField(
        verbose_name=_("representee auth value"),
        help_text=_("Value of the identifier for the submission authentication."),
        max_length=250,
    )
    representee_branch_number = models.CharField(
        _("representee KvK branch number"),
        max_length=12,
        blank=True,
        help_text=_(
            "Optional branch number of the company identified by KVK. Note that this "
            "may only be provided if the auth attribute is 'kvk'."
        ),
    )

    ttl = models.PositiveSmallIntegerField(
        _("ttl (in hours)"),
        help_text=_(
            "Time-to-live in hours. The expiry date is calculated from the creation "
            "timestamp plus the TTL. After this moment, the submission data will be "
            "deleted. A submission should be started within this TTL."
        ),
        # 1 week TTL max - this is a conservative default. If feedback comes in that
        # this is too low, we can definitely reconsider.
        validators=[MaxValueValidator(24 * 7)],
    )

    # audit/metadata
    owner = models.ForeignKey[User](
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("owner"),
        help_text=_("(API) user who owns the object. Used in permission checks."),
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)

    get_representee_auth_attribute_display: Callable[[], str]

    class Meta:
        verbose_name = _("initial submission data")
        verbose_name_plural = _("initial submission data")
        constraints = (
            models.CheckConstraint(
                name="branch_number_only_when_auth_attribute_kvk",
                condition=(
                    ~models.Q(representee_auth_attribute=SupportedAuthAttributes.kvk)
                    & models.Q(representee_branch_number="")
                )
                | models.Q(representee_auth_attribute=SupportedAuthAttributes.kvk),
            ),
        )

    def __str__(self) -> str:
        return _("{attribute} for {form}").format(
            attribute=self.get_representee_auth_attribute_display(),
            form=self.form.admin_name if self.form else "?",
        )

    @property
    def expiry_date(self) -> datetime:
        return self.created_on + timedelta(hours=self.ttl)
