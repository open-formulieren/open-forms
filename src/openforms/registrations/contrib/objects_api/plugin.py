from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from typing_extensions import override

from openforms.registrations.utils import execute_unless_result_exists
from openforms.utils.date import get_today

from ...base import BasePlugin
from ...registry import register
from .checks import check_config
from .client import get_objects_client
from .config import ObjectsAPIOptionsSerializer
from .models import ObjectsAPIConfig
from .registration_variables import Registry, register as variables_registry
from .submission_registration import HANDLER_MAPPING
from .typing import RegistrationOptions

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


PLUGIN_IDENTIFIER = "objects_api"

logger = logging.getLogger(__name__)


def build_options(plugin_options: RegistrationOptions, key_mapping: dict) -> dict:
    """
    Construct options from plugin options dict, allowing renaming of keys
    """
    options = {
        new_key: plugin_options[key_in_opts]
        for new_key, key_in_opts in key_mapping.items()
        if key_in_opts in plugin_options
    }
    return options


@register(PLUGIN_IDENTIFIER)
class ObjectsAPIRegistration(BasePlugin):
    verbose_name = _("Objects API registration")
    configuration_options = ObjectsAPIOptionsSerializer

    @override
    def register_submission(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict[str, Any]:
        """Register a submission using the Objects API backend.

        Depending on the options version (legacy or mapped variables), the payload
        will be created differently. The actual logic lives in the ``submission_registration`` submodule.
        """

        config = ObjectsAPIConfig.get_solo()
        assert isinstance(config, ObjectsAPIConfig)
        config.apply_defaults_to(options)

        handler = HANDLER_MAPPING[options["version"]]

        object_data = handler.get_object_data(
            submission=submission,
            options=options,
        )

        with get_objects_client() as objects_client:
            response = execute_unless_result_exists(
                partial(objects_client.create_object, object_data=object_data),
                submission,
                "intermediate.objects_api_object",
            )

        return response

    @override
    def check_config(self):
        check_config()

    @override
    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:registrations_objects_api_objectsapiconfig_change",
                    args=(ObjectsAPIConfig.singleton_instance_id,),
                ),
            ),
        ]

    @override
    def get_custom_templatetags_libraries(self) -> list[str]:
        prefix = "openforms.registrations.contrib.objects_api.templatetags.registrations.contrib"
        return [
            f"{prefix}.objects_api.json_tags",
        ]

    @override
    def update_payment_status(
        self, submission: Submission, options: RegistrationOptions
    ) -> None:
        config = ObjectsAPIConfig.get_solo()
        assert isinstance(config, ObjectsAPIConfig)
        config.apply_defaults_to(options)

        if not options["payment_status_update_json"]:
            logger.warning(
                "Skipping payment status update because no template was configured."
            )
            return

        handler = HANDLER_MAPPING[options["version"]]
        updated_object_data = handler.get_update_payment_status_data(
            submission, options
        )

        updated_object_data = {
            "record": {
                "data": updated_object_data,
                "startAt": get_today(),
            },
        }

        object_url = submission.registration_result["url"]
        with get_objects_client() as objects_client:
            response = objects_client.patch(
                url=object_url,
                json=updated_object_data,
                headers={"Content-Crs": "EPSG:4326"},
            )
            response.raise_for_status()

    @override
    def get_variables_registry(self) -> Registry:
        return variables_registry
