"""
Base implementation for timestamped salted HMAC tokens.
"""

from abc import ABC, abstractmethod
from datetime import date

from django.conf import settings
from django.db import models
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36


class BaseTokenGenerator(ABC):
    """
    Generate and check tokens for object-level permission checks.

    Implementation adapted from
    :class:`django.contrib.auth.tokens.PasswordResetTokenGenerator`.

    When using timestamped tokens, keep in mind that:

    * the token should be single-use - once used/consumed, an attribute on the object
      should have been mutated that invalidates the token on replays.
    * the token expires automatically after a number of days, either configured through
      Django settings or information defined on the (related) object.
    * Expiry/validity is expressed in number of days - that's the resolution. A token
      generated shortly before midnight is still valid for the following day.
    * the Django ``settings.SECRET_KEY`` is used to protect against tampering. KEEP
      IT SECRET.

    **Implementation guidelines**

    Subclasses MUST:

    * specify :attr:`key_salt` - the salt to use for all tokens, input to
      :func:`salted_hmac`
    * specify :attr:`token_timeout_days`, determining how long the token is valid.
    * implement :meth:`get_hash_value_parts`
    """

    secret = settings.SECRET_KEY
    key_salt: str = ""
    """
    Value to use as salt for the hashing process.
    """
    token_timeout_days = 1
    """
    Default number of days the token is valid. Can be overridden via
    :meth:`get_token_timeout_days`.
    """

    def make_token(self, obj: models.Model) -> str:
        """
        Return a token that expires or gets invalidated by state changes.
        """
        num_days = self._num_days(date.today())
        return self._make_token_with_timestamp(obj, num_days)

    def check_token(self, obj: models.Model, token: str) -> bool:
        """
        Check that the token is (still) valid for the given model instance.
        """

        if not (obj and token):
            return False

        # parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        valid_token = self._make_token_with_timestamp(obj, ts)
        if not constant_time_compare(valid_token, token):
            return False

        # Check the timestamp is within limit. Timestamps are rounded to
        # midnight (server time) providing a resolution of only 1 day. If a
        # link is generated 5 minutes before midnight and used 6 minutes later,
        # that counts as 1 day. Therefore, timeout_days = 1 means
        # "at least 1 day, could be up to 2."
        timeout_days = self.get_token_timeout_days(obj)
        num_days = self._num_days(date.today())
        if (num_days - ts) > timeout_days:
            return False

        return True

    def get_token_timeout_days(self, obj: models.Model) -> int:
        """
        Determine how many days the token is valid for.

        Defaults to :attr:`token_timeout_days`, optionally you can override this method
        and fetch information from the object being checked.
        """
        return self.token_timeout_days

    @abstractmethod
    def get_hash_value_parts(self, obj: models.Model) -> list[str]:
        """
        Obtain a list of strings reflecting object state.

        Token invalidation relies on this. Instance attribute values that mutate on
        token consumption should be returned here. For example, for a password reset
        token, the hashed password value should be included since the hash changes
        when the password is reset (even with the same value!).

        The code protected with the token should have side-effects that change the
        values returned here, if the token should invalidate after consumption.
        """
        raise NotImplementedError()

    def _make_token_with_timestamp(self, obj: models.Model, timestamp: int) -> str:
        # timestamp is number of days since 2020-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2141
        ts_b36 = int_to_base36(timestamp)
        hash_string = salted_hmac(
            self.key_salt,
            self._make_hash_value(obj, timestamp),
            secret=self.secret,
        ).hexdigest()[::2]  # Limit to 20 characters to shorten the URL.
        return f"{ts_b36}-{hash_string}"

    def _make_hash_value(self, obj: models.Model, timestamp: int) -> str:
        """
        Obtain and hash obj state properties.

        Token consumption should mutate the obtained state properties, leading to
        token invalidation. Failing that, eventually :attr:`token_timeout_days` will
        invalidate the token.
        """
        parts = self.get_hash_value_parts(obj)
        assert all(isinstance(bit, str) for bit in parts), (
            "All hash value parts should be strings."
        )
        joined_parts = "".join(parts)
        return f"{joined_parts}{timestamp}"

    def _num_days(self, dt: date) -> int:
        """
        Return the number of days between 01-01-2020 and today
        """
        return (dt - date(2020, 1, 1)).days
