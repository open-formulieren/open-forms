from dataclasses import dataclass

import clamd


def remove_empty_design_tokens(obj: dict) -> dict:
    if "value" in obj:
        return obj

    result = {}
    for key, value in obj.items():
        if not isinstance(value, dict):
            continue
        updated_value = remove_empty_design_tokens(value)
        # empty object -> remove it by not including it anymore
        if not updated_value:
            continue

        result[key] = updated_value

    return result


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
