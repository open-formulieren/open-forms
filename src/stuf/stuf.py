"""
Model SOAP/StUF-concepts in the Python domain.
"""

from dataclasses import dataclass
from typing import Literal

from .models import StufService


@dataclass
class WSSecurity:
    """
    Capture WS-Security configuration.

    .. note:: when using :module:`zeep`, there are built-in constructs. Prefer using
       zeep or any other SOAP library over doing this template-based with Django!
    """

    use_wss: bool
    wss_username: str
    wss_password: str


@dataclass
class InvolvedParty:
    applicatie: str
    organisatie: str = ""
    administratie: str = ""
    gebruiker: str = ""

    NAMES = (
        "applicatie",
        "organisatie",
        "administratie",
        "gebruiker",
    )

    @classmethod
    def from_service_configuration(
        cls,
        service: StufService,
        prefix: Literal["zender", "ontvanger"],
    ) -> "InvolvedParty":
        kwargs = {name: getattr(service, f"{prefix}_{name}", "") for name in cls.NAMES}
        return cls(**kwargs)


@dataclass
class StuurGegevens:
    zender: InvolvedParty
    ontvanger: InvolvedParty
