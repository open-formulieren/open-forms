from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from openforms.config.models import GlobalConfiguration
from openforms.emails.constants import URL_REGEX
from openforms.emails.utils import get_system_netloc_allowlist


class URLSanitationValidator:
    def __call__(self, value):
        """
        this operation matches the logic of .utils.sanitize_content()
        """
        config = GlobalConfiguration.get_solo()

        allowlist = (
            get_system_netloc_allowlist() + config.email_template_netloc_allowlist
        )

        for m in URL_REGEX.finditer(value):
            parsed = urlparse(m.group())
            if parsed.netloc not in allowlist:
                raise ValidationError(
                    _(
                        "This domain is not in the global netloc allowlist: {netloc}"
                    ).format(netloc=parsed.netloc)
                )
