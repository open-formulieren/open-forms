from typing import assert_never

import structlog

from openforms.contrib.haal_centraal.clients import get_brp_client
from openforms.contrib.haal_centraal.clients.brp import NaturalPersonDetails

from .constants import FamilyMembersTypeChoices
from .filters import filter_members_by_age
from .typing import FamilyMemberOptions

logger = structlog.stdlib.get_logger(__name__)


def get_data_from_haal_centraal(
    bsn: str, options: FamilyMemberOptions
) -> list[NaturalPersonDetails]:
    with get_brp_client() as client:
        match options["type"]:
            case FamilyMembersTypeChoices.partners:
                return client.get_family_members(
                    bsn,
                    include_partner=True,
                    include_children=False,
                )
            case FamilyMembersTypeChoices.children:
                children = client.get_family_members(
                    bsn,
                    include_partner=False,
                    include_children=True,
                    include_deceased=options["include_deceased"],
                )

                return list(
                    filter_members_by_age(
                        children,
                        min_age=options["min_age"],
                        max_age=options["max_age"],
                    )
                )
            case _:  # pragma: no cover
                assert_never(options["type"])
