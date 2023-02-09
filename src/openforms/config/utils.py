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


def verify_clamav_connection(host: str, port: int, timeout: int) -> dict:
    scanner = clamd.ClamdNetworkSocket(
        host=host,
        port=port,
        timeout=timeout,
    )
    try:
        result = scanner.ping()
    except clamd.ConnectionError as exc:
        return {"can_connect": False, "error": exc.args[0]}

    if result == "PONG":
        return {"can_connect": True, "error": ""}

    return {"can_connect": False, "error": result}
