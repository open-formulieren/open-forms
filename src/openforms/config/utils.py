from dataclasses import dataclass

import clamd

from .constants import CSPDirective


@dataclass
class CSPEntry:
    directive: CSPDirective
    value: str
    identifier: str = ""


@dataclass
class ClamAVStatus:
    can_connect: bool
    error: str = ""


def verify_clamav_connection(host: str, port: int, timeout: int) -> "ClamAVStatus":
    scanner = clamd.ClamdNetworkSocket(
        host=host,
        port=port,
        timeout=timeout,
    )
    try:
        result = scanner.ping()
    except clamd.ConnectionError as exc:
        return ClamAVStatus(can_connect=False, error=exc.args[0])

    if result == "PONG":
        return ClamAVStatus(can_connect=True)

    return ClamAVStatus(can_connect=False, error=result)
