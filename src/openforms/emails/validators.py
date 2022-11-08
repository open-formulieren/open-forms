from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from mail_cleaner.constants import URL_REGEX


@deconstructible
class URLSanitationValidator:
    message = _("This domain is not in the global netloc allowlist: {netloc}")

    def __call__(self, value):
        """
        Validate that only allowed domains are present as URLs.

        This operation matches the logic of
        :func:`openforms.emails.utils.sanitize_content`.
        """

        # local imports because we use this on GlobalConfiguration itself
        from openforms.config.models import GlobalConfiguration
        from openforms.emails.utils import get_system_netloc_allowlist

        config = GlobalConfiguration.get_solo()

        allowlist = (
            get_system_netloc_allowlist() + config.email_template_netloc_allowlist
        )

        for m in URL_REGEX.finditer(value):
            parsed = urlsplit(m.group())
            if parsed.netloc not in allowlist:
                raise ValidationError(
                    self.message.format(netloc=parsed.netloc), code="invalid"
                )
