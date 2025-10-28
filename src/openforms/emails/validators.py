from collections.abc import Iterable
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from mail_cleaner.constants import URL_REGEX


def subdomains(domain: str) -> Iterable[str]:
    """
    Return an iterable with all the subdomains for a particular domain.

    For example, for open-forms.test.maykin.nl, this would return
    {'open-forms.test.maykin.nl', 'nl', 'maykin.nl', 'test.maykin.nl'}
    """
    domain_bits_reversed = domain.split(".")[::-1]
    subdomains_split = [domain_bits_reversed[0]]
    for domain_bit in domain_bits_reversed[1:]:
        subdomains_split.append(".".join([domain_bit, subdomains_split[-1]]))
    return set(subdomains_split)


@deconstructible
class URLSanitationValidator:
    message = _("This domain is not in the global netloc allowlist: {netloc}")

    def __call__(self, value):
        """
        Validate that only allowed domains are present as URLs.

        This operation matches the logic of
        :func:`openforms.emails.utils.sanitize_content`.
        """
        from .utils import get_netloc_allowlist
        # local imports because we use this on GlobalConfiguration itself

        allowlist = get_netloc_allowlist()

        for m in URL_REGEX.finditer(value):
            parsed = urlsplit(m.group())

            if not any(stem for stem in subdomains(parsed.netloc) if stem in allowlist):
                raise ValidationError(
                    self.message.format(netloc=parsed.netloc), code="invalid"
                )
