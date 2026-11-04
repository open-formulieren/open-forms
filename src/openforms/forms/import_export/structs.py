"""
Struct definitions for import/export resources.

The structs validate the contents of the export artifacts on a high level. The actual
contents of the resources are validated with the import/export serializers, see
:mod:`openforms.forms.import_export.serializers`.
"""

import zipfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from os import PathLike
from typing import (  # Any because we don't want msgspec to deeply decode contents
    Any,
    Literal,
    Protocol,
    overload,
)

from django.conf import settings
from django.utils import timezone
from django.utils.safestring import SafeString

import msgspec
from rest_framework.relations import Hyperlink
from tablib import Dataset

from openforms.typing import JSONObject

__all__ = ["Artifact", "ExportMeta"]


def _enc_hook(obj: Any) -> Any:
    """
    Encode non-native msgspec types.
    """
    match obj:
        case Dataset():
            return obj.dict
        case Hyperlink():
            return str(obj)
        case SafeString():
            return obj[:]
        case _:  # pragma: no cover
            raise NotImplementedError(f"Objects of type {type(obj)} are not supported")


json_encoder = msgspec.json.Encoder(enc_hook=_enc_hook)


def _dec_hook(type: type, obj: Any) -> Any:
    """
    Decode JSON into non-native msgspec types.
    """
    if type is Dataset:
        breakpoint()
    raise NotImplementedError(
        f"Objects of type {type} are not supported"
    )  # pragma: no cover


json_decoder = msgspec.json.Decoder(dec_hook=_dec_hook, strict=True)


class ZipWritable(Protocol):
    # effectively the same as _ZipWritable from the typeshed
    def write(self, data: bytes, /) -> int: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...


class ExportMeta(msgspec.Struct, kw_only=True, frozen=True):
    of_release: str | None = msgspec.field(default_factory=lambda: settings.RELEASE)
    of_git_sha: str | None = msgspec.field(default_factory=lambda: settings.GIT_SHA)
    created: datetime = msgspec.field(default_factory=timezone.now)


class Artifact(msgspec.Struct, kw_only=True, rename="camel"):
    """
    A single form export/import artifact.
    """

    _meta: ExportMeta = ExportMeta()
    # TODO: ideally this would be a singular object, not a collection - as there must
    # always be exactly one form present.
    forms: list[JSONObject]
    form_steps: list[JSONObject]
    form_definitions: list[JSONObject]
    form_logic: list[JSONObject]
    form_variables: list[JSONObject]
    # supporting additional resources not directly owned by a form
    product: Dataset | msgspec.UnsetType = msgspec.UNSET
    wms_tile_layers: Dataset | msgspec.UnsetType = msgspec.UNSET
    wmts_tile_layers: Dataset | msgspec.UnsetType = msgspec.UNSET
    yivi_attribute_groups: Dataset | msgspec.UnsetType = msgspec.UNSET

    @overload
    def as_resources_mapping(self, *, encode: Literal[True]) -> Mapping[str, bytes]: ...

    @overload
    def as_resources_mapping(
        self, *, encode: Literal[False]
    ) -> Mapping[str, Sequence[JSONObject]]: ...

    def as_resources_mapping(
        self, *, encode: bool = False
    ) -> Mapping[str, bytes | Sequence[JSONObject]]:
        """
        Output the mapping of resource name to JSON-encoded resource data.
        """
        resources = msgspec.to_builtins(self, enc_hook=_enc_hook)
        return {
            key: json_encoder.encode(value) if encode else value
            for key, value in resources.items()
        }

    def write_zip(self, target: str | PathLike[str] | ZipWritable) -> None:
        """
        Write the artifact resources a ZIP export file.
        """
        resources = self.as_resources_mapping(encode=True)
        with zipfile.ZipFile(target, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", data)
