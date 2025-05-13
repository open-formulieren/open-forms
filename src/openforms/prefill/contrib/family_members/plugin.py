from typing import assert_never

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog

from openforms.authentication.service import AuthAttribute
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.checks import (
    check_config as check_haal_centraal_config,
)
from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable
from stuf.stuf_bg.checks import check_config as check_stuf_bg_config

from ...base import BasePlugin
from ...registry import register
from .config import FamilyMembersOptionsSerializer
from .haal_centraal import get_data_from_haal_centraal
from .stuf_bg import get_data_from_stuf_bg
from .typing import FamilyMembersChildOptions, FamilyMembersPartnerOptions

logger = structlog.stdlib.get_logger(__name__)

PLUGIN_IDENTIFIER = "family_members"


@register(PLUGIN_IDENTIFIER)
class FamilyMembersPrefill(
    BasePlugin[FamilyMembersPartnerOptions | FamilyMembersChildOptions]
):
    verbose_name = _("Family members")
    requires_auth = (AuthAttribute.bsn,)
    options = FamilyMembersOptionsSerializer

    @staticmethod
    def _get_handler():
        """
        Return the suitable handler according to the desired method of data retrieving.
        """
        handlers: dict = {
            FamilyMembersDataAPIChoices.haal_centraal: get_data_from_haal_centraal,
            FamilyMembersDataAPIChoices.stuf_bg: get_data_from_stuf_bg,
        }
        config = GlobalConfiguration.get_solo()
        return handlers[config.family_members_data_api]

    @classmethod
    def get_prefill_values_from_options(
        cls,
        submission: Submission,
        options: FamilyMembersPartnerOptions | FamilyMembersChildOptions,
        submission_value_variable: SubmissionValueVariable,
    ) -> dict[str, JSONEncodable]:
        if not submission.is_authenticated or not (
            cls.requires_auth and submission.auth_info.attribute in cls.requires_auth
        ):
            return {}

        assert submission_value_variable.form_variable
        initial_data_form_variable = submission_value_variable.form_variable.key
        form_variable_to_update = options["mutable_data_form_variable"]
        bsn = submission.auth_info.value
        handler = cls._get_handler()
        results = handler(bsn, options)

        # we need to update both variables (the one that contains the initial data and the
        # prefill configuration and the mutable one) with the data that we have retrieved
        return {initial_data_form_variable: results, form_variable_to_update: results}

    def check_config(self):
        config = GlobalConfiguration.get_solo()

        match config.family_members_data_api:
            case FamilyMembersDataAPIChoices.haal_centraal:
                check_haal_centraal_config()
            case FamilyMembersDataAPIChoices.stuf_bg:
                check_stuf_bg_config()
            case _:  # pragma: no cover
                assert_never(config.family_members_data_api)

    def get_config_actions(self):
        return [
            (
                _("Manage Family members data retrieval"),
                reverse("admin:config_globalconfiguration_change"),
            ),
        ]
