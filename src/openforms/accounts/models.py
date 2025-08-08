from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from openforms.translations.utils import get_supported_languages

from .managers import UserManager


def get_ui_languages() -> list[tuple[str, str]]:
    languages = get_supported_languages()
    return [(language.code, language.name) for language in languages]


class User(AbstractBaseUser, PermissionsMixin):
    """
    Use the built-in user model.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=255, blank=True)
    last_name = models.CharField(_("last name"), max_length=255, blank=True)
    email = models.EmailField(_("email address"), blank=True)

    employee_id = models.CharField(
        _("employee id"),
        max_length=150,
        blank=True,
        help_text=_("Employee identification in the organisation."),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    # user preferences
    ui_language = models.CharField(
        _("UI language"),
        max_length=10,
        choices=get_ui_languages(),
        default="",
        blank=True,
        help_text=_(
            "Preferred (admin) UI language. If unset, your browser preferences are "
            "respected."
        ),
    )

    objects: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        UserManager
    ] = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        constraints = [
            models.UniqueConstraint(
                fields=["email"], condition=~Q(email=""), name="filled_email_unique"
            )
        ]
        permissions = (
            ("email_backend_test", _("Can use email backend test")),
            ("configuration_overview", _("Can access configuration overview")),
        )

    def get_full_name(self) -> str:
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def get_employee_name(self):
        "Best effort to get something presentable"
        return self.get_full_name() or self.employee_id or self.username


class UserPreferences(User):
    """
    Expose the user model for preference-editing in a separate admin entry.
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        proxy = True
        verbose_name = _("user preferences")
        verbose_name_plural = _("user preferences")
