from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _


validate_digits = RegexValidator(
    regex='^[0-9]+$', message=_('Waarde moet numeriek zijn.')
)


@deconstructible
class BSNValidator:
    error_messages = {
        'too_short': _('BSN moet 9 tekens lang zijn.'),
        'wrong': _('Onjuist BSN.')
    }

    def __call__(self, value):
        """
        Validates that a string value is a valid BSN number by applying the
        '11-proef' checking.

        :param value: String object representing a presumably good BSN number.
        """
        # Initial sanity checks.
        validate_digits(value)
        if len(value) != 9:
            raise ValidationError(self.error_messages['too_short'])

        # 11-proef check.
        total = 0
        for multiplier, char in enumerate(reversed(value), start=1):
            if multiplier == 1:
                total += -multiplier * int(char)
            else:
                total += multiplier * int(char)

        if total % 11 != 0:
            raise ValidationError(self.error_messages['wrong'])


validate_bsn = BSNValidator()
