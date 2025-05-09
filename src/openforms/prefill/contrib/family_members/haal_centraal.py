from collections import defaultdict

import structlog

from openforms.contrib.haal_centraal.clients import get_brp_client
from openforms.contrib.haal_centraal.clients.brp import NaturalPersonDetails
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig

from .constants import FamilyMembersTypeChoices
from .filters import filter_members_by_age
from .typing import FamilyMembersChildOptions, FamilyMembersPartnerOptions
from .utils import covert_to_json_serializable

logger = structlog.stdlib.get_logger(__name__)


def get_data_from_haal_centraal(
    bsn: str, options: FamilyMembersPartnerOptions | FamilyMembersChildOptions
) -> dict[str, dict[str, list[NaturalPersonDetails]]]:
    variable_key = options["form_variable"]
    results: defaultdict[str, dict[str, list[NaturalPersonDetails]]] = defaultdict(dict)

    with get_brp_client() as client:
        config = HaalCentraalConfig.get_solo()
        hc_version = config.brp_personen_version.value
        if not hc_version == BRPVersions.v20:
            logger.warning(
                "The selected version of HaalCentraal is not supported.",
            )
            return {}

        if options["type"] == FamilyMembersTypeChoices.partners:
            results[variable_key]["partners"] = client.get_family_members(
                bsn, include_partner=True, include_children=False
            )
        elif options["type"] == FamilyMembersTypeChoices.children:
            include_deceased = options.get("include_deceased")
            results[variable_key]["children"] = client.get_family_members(
                bsn,
                include_partner=False,
                include_children=True,
                include_deceased=include_deceased if include_deceased else False,
            )

            min_age = options.get("min_age")
            max_age = options.get("max_age")

            children_list = results[variable_key]["children"]

            # no filters needed
            if not (min_age or max_age):
                results[variable_key]["children"] = children_list
                serializable_data = covert_to_json_serializable(results)
                return serializable_data

            results[variable_key]["children"] = filter_members_by_age(
                children_list, min_age=min_age, max_age=max_age
            )

    serializable_data = covert_to_json_serializable(results)

    return serializable_data
