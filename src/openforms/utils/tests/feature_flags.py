from copy import deepcopy

from django.conf import settings
from django.test import override_settings


def _set_feature_flag(flag: str, value: bool):
    assert flag in settings.FLAGS, f"Flag {flag} is not defined in settings.FLAGS"
    flags = {
        **deepcopy(settings.FLAGS),
        flag: [
            {
                "condition": "boolean",
                "value": value,
                "required": False,
            }
        ],
    }
    return override_settings(FLAGS=flags)


def enable_feature_flag(flag: str):
    return _set_feature_flag(flag, True)


def disable_feature_flag(flag: str):
    return _set_feature_flag(flag, False)
