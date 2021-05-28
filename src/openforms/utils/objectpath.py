import typing


class PathResolveError(KeyError):
    pass


def resolve_object_path(obj: typing.Mapping, path: str) -> typing.Any:
    fragments = path.split("__")
    for key in fragments:
        if not key:
            raise PathResolveError(f"cannot resolve empty fragment from '{path}'")

        try:
            obj = obj[key]
        except TypeError as e:
            raise PathResolveError(f"bad fragment '{key}' from '{path}'") from e
        except KeyError as e:
            raise PathResolveError(
                f"cannot resolve fragment '{key}' from '{path}'"
            ) from e

    return obj
