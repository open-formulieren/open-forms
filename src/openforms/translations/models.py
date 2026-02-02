from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from privates.fields import PrivateMediaFileField

from .constants import StatusChoices
from .utils import get_supported_languages


def get_app_release() -> str:
    return settings.RELEASE or ""


def get_language_choices() -> list[tuple[str, str]]:
    languages = get_supported_languages()
    return [(lang.code, lang.name) for lang in languages]


class TranslationsMetaData(models.Model):
    language_code = models.CharField(
        _("language"),
        max_length=10,
        choices=get_language_choices(),
        unique=True,
        help_text=_("Selected language."),
    )
    messages_file = PrivateMediaFileField(
        _("messages JSON file"),
        upload_to="messages/uploaded/%Y/%m/%d",
        blank=True,
        help_text=_("JSON file containing user's custom translations."),
    )
    compiled_asset = PrivateMediaFileField(
        _("compiled translations JSON file"),
        upload_to="messages/compiled/%Y/%m/%d",
        editable=False,
        help_text=_(
            "JSON file containing user's custom translations after it has been "
            "successfully compiled."
        ),
    )
    processing_status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.pending,
        help_text=_("The status of the uploaded custom translations JSON file."),
    )
    debug_output = models.TextField(
        _("output from the processing phase"),
        blank=True,
        help_text=_(
            "The output from the processing phase, useful for debugging purposes."
        ),
    )
    last_updated = models.DateTimeField(
        _("last updated"),
        blank=True,
        null=True,
        help_text=_(
            "Keeps track of the last successful processing of the uploaded file. "
            "Useful for understanding since when the custom translations are "
            "active."
        ),
    )
    messages_count = models.IntegerField(
        _("number of custom messages"),
        editable=False,
        blank=True,
        null=True,
        help_text=_(
            "How many custom messages are included, this is set once processing "
            "completes successfully."
        ),
    )
    app_release = models.CharField(
        _("application version"),
        max_length=50,
        blank=True,
        editable=False,
        default=get_app_release,
        help_text=_(
            "App release/version at the time the messages were added, updated or "
            "activated."
        ),
    )

    class Meta:
        verbose_name = _("translation metadata")
        verbose_name_plural = _("translation metadata")

    def __str__(self):
        return _("Metadata for translations in {language_code}").format(
            language_code=self.language_code
        )
