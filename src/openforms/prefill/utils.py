from typing import Any

from glom import Path, PathAccessError, glom


def find_in_dicts(*dicts: dict[str, Any], path: Path) -> str | None:
    """
    Given a specific path, look up the value in the specified sequence of dictionaries.

    :param dicts: a sequence of dictionaries to look up in.
    :param path: an :class:`Path` instance which contains the segments of the path.
    :return: an str (the found value) or None.
    """
    for data in dicts:
        try:
            return glom(data, path)
        except PathAccessError:
            continue
