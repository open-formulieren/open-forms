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
