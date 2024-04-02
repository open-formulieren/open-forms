def _normalize_pattern(pattern: str) -> str:
    """
    Normalize a regex pattern so that it matches from beginning to the end of the value.
    """
    if not pattern.startswith("^"):
        pattern = f"^{pattern}"
    if not pattern.endswith("$"):
        pattern = f"{pattern}$"
    return pattern
