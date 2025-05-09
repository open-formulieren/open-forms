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
from openforms.typing import JSONEncodable
from stuf.stuf_bg.checks import check_config as check_stuf_bg_config

from ...base import BasePlugin
from ...registry import register
from .api.serializers import FamilyMembersOptionsSerializer
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
    ) -> dict[str, JSONEncodable]:
        if not submission.is_authenticated or not (
            cls.requires_auth and submission.auth_info.attribute in cls.requires_auth
        ):
            return {}

        bsn = submission.auth_info.value
        handler = cls._get_handler()
        results = handler(bsn, options)

        return results

    def check_config(self):
        config = GlobalConfiguration.get_solo()
        if config.family_members_data_api == FamilyMembersDataAPIChoices.haal_centraal:
            check_haal_centraal_config()
        elif FamilyMembersDataAPIChoices.stuf_bg:
            check_stuf_bg_config()

    def get_config_actions(self):
        return [
            (
                _("Manage Family members data retrieval"),
                reverse("admin:config_globalconfiguration_change"),
            ),
        ]
