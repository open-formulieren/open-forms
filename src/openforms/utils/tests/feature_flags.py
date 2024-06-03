from copy import deepcopy

from django.conf import settings
from django.test import override_settings


def enable_feature_flag(flag: str):
    assert flag in settings.FLAGS, f"Flag {flag} is not defined in settings.FLAGS"
    flags = {
        **deepcopy(settings.FLAGS),
        flag: [
            {
                "condition": "boolean",
                "value": True,
                "required": False,
            }
        ],
    }
    return override_settings(FLAGS=flags)
