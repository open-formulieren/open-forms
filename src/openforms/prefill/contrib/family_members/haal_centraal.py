from collections import defaultdict

import structlog

from openforms.contrib.haal_centraal.clients import get_brp_client
from openforms.contrib.haal_centraal.clients.brp import NaturalPersonDetails
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig

from .constants import FamilyMembersTypeChoices
from .filters import filter_members_by_age
from .typing import FamilyMembersChildOptions, FamilyMembersPartnerOptions
from .utils import convert_to_json_serializable

logger = structlog.stdlib.get_logger(__name__)


def get_data_from_haal_centraal(
    bsn: str,
    options: FamilyMembersPartnerOptions | FamilyMembersChildOptions,
) -> dict[str, list[NaturalPersonDetails]]:
    config = HaalCentraalConfig.get_solo()
    hc_version = config.brp_personen_version
    if not hc_version == BRPVersions.v20:
        logger.warning(
            "unsupported_version",
            plugin_id="haal_centraal",
            version=BRPVersions.v13,
        )
        return {}

    results: defaultdict[str, list[NaturalPersonDetails]] = defaultdict(list)

    with get_brp_client() as client:
        match options["type"]:
            case FamilyMembersTypeChoices.partners:
                partners_list = client.get_family_members(
                    bsn, include_partner=True, include_children=False
                )
                results[options["type"]] = partners_list
                return convert_to_json_serializable(results)
            case FamilyMembersTypeChoices.children:
                include_deceased = options.get("include_deceased", True)

                children_list = client.get_family_members(
                    bsn,
                    include_partner=False,
                    include_children=True,
                    include_deceased=(
                        include_deceased if include_deceased is not None else True
                    ),
                )

                min_age = options.get("min_age")
                max_age = options.get("max_age")

                # no filters needed
                if not (min_age or max_age):
                    results[options["type"]] = children_list
                    return convert_to_json_serializable(results)

                filtered_results = filter_members_by_age(
                    children_list, min_age=min_age, max_age=max_age
                )
                results[options["type"]] = filtered_results
                return convert_to_json_serializable(results)
