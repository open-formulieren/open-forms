import json
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder

import structlog

logger = structlog.stdlib.get_logger(__name__)


def to_json(obj: Any):
    return json.dumps(obj, cls=DjangoJSONEncoder)


def remove_key_from_dict(dictionary, key):
    for dict_key in list(dictionary.keys()):
        if key == dict_key:
            del dictionary[key]
        elif isinstance(dictionary[dict_key], dict):
            remove_key_from_dict(dictionary[dict_key], key)
        elif isinstance(dictionary[dict_key], list):
            for value in dictionary[dict_key]:
                if isinstance(value, dict):
                    remove_key_from_dict(value, key)
