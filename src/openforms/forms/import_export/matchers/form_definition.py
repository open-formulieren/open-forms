import hashlib
import json

from openforms.forms.models import FormDefinition
from openforms.typing import JSONObject, JSONValue


def normalize_configuration(value: JSONValue) -> JSONValue:
    """
    Normalize the form configuration by removing the "id" field from all components.
    """
    if isinstance(value, dict):
        return {
            key: normalize_configuration(child)
            for key, child in value.items()
            if key != "id"
        }

    if isinstance(value, list):
        return [normalize_configuration(child) for child in value]

    return value


def configuration_fingerprint(configuration: JSONObject) -> str:
    """
    Turn form definition configuration into a fingerprint.
    """
    normalized = normalize_configuration(configuration)

    serialized = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class FormDefinitionMatcher:
    def __init__(self):
        self._instances_by_configuration = self._build_lookup()

    def _build_lookup(self) -> dict[str, list[FormDefinition]]:
        result: dict[str, list[FormDefinition]] = {}

        for instance in (fd for fd in FormDefinition.objects.all() if fd.is_reusable):
            key = configuration_fingerprint(instance.configuration)
            result.setdefault(key, []).append(instance)

        return result

    def find(self, configuration: JSONObject) -> FormDefinition | None:
        expected_fingerprint = configuration_fingerprint(configuration)
        matches = self._instances_by_configuration.get(expected_fingerprint, None)

        return matches[0] if matches else None
