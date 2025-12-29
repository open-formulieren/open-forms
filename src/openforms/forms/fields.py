from typing import Any

from django.db import models

import msgspec

from formio_types import FormioConfiguration
from formio_types.datetime import FormioDateTime


def dec_hook(type_: type, obj: Any):
    if type_ is FormioDateTime and isinstance(obj, str):
        return FormioDateTime.fromstr(obj)

    return obj


def enc_hook(obj: Any):
    if isinstance(obj, FormioDateTime):
        return obj.actual_value
    return obj


class FormioConfigurationField(models.JSONField):
    """
    Optimized JSONField for Formio form definitions.

    Uses :mod:`msgspec` decoding and encoding under the hood for serializing and
    deserializing the ``jsonb`` data.
    """

    def from_db_value(self, value: str | None, expression, connection):
        """
        Replace stdlib json.loads with msgspec.

        Only support PostgreSQL.
        """
        if value is None:
            return value
        return msgspec.json.decode(value, type=FormioConfiguration, dec_hook=dec_hook)

    def get_db_prep_value(self, value, connection, prepared=False):
        # return connection.ops.adapt_json_value(value, self.encoder) is key to use a
        # different dumps function (!)
        if isinstance(value, msgspec.Struct):
            value = msgspec.to_builtins(value, enc_hook=enc_hook)
        return super().get_db_prep_value(value, connection, prepared=prepared)
