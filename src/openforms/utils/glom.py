from glom import Path

__all__ = ["_glom_path_to_str"]


def _glom_path_to_str(path: Path) -> str:
    """
    '.'-join a glom path instance.

    Note that the correctness is limited to path bits that don't include dots, i.e.
    Path.from_text(glom_path_to_string(path)) is **not** guaranteed to be invariant.

    This function exists solely because of Github issue #2699 and may not be used
    outside of this context. It will be refactored in #2713.
    """
    return ".".join([str(value) for value in path.values()])
