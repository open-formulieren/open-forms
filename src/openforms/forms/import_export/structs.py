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
    Self,
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


type ShallowJSONObject = dict[str, Any]
"""
A non-recursive JSON-like object.

msgspec requires the type annotations to be able to decode/convert from stream/builtins.
A type of ``dict[str, object]`` (to avoid the ``Any``) is not supported. Note that the
resulting dicts/lists are fed downstream to the import serializers for proper conversion
with backwards compatibility shims, and to produce better error messages.
"""


def _enc_hook(obj: object) -> object:
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


def _dec_hook(type: type, obj: object) -> object:
    """
    Decode JSON into non-native msgspec types.
    """
    if type is Dataset:
        dataset = Dataset()
        dataset.dict = obj
        return dataset
    raise NotImplementedError(
        f"Objects of type {type} are not supported"
    )  # pragma: no cover


json_decoder = msgspec.json.Decoder(dec_hook=_dec_hook, strict=True)


class ZipWritable(Protocol):
    # effectively the same as _ZipWritable from the typeshed
    def write(self, data: bytes, /) -> int: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...


class ZipReadable(Protocol):
    # effectively the same as ZipReadable from the typeshed
    def seek(self, offset: int, whence: int = 0, /) -> int: ...
    def read(self, n: int = -1, /) -> bytes: ...


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
    forms: list[ShallowJSONObject]
    form_steps: list[ShallowJSONObject] = []
    form_definitions: list[ShallowJSONObject] = []
    form_logic: list[ShallowJSONObject] = []
    form_variables: list[ShallowJSONObject] = []
    # supporting additional resources not directly owned by a form
    product: Dataset | msgspec.UnsetType = msgspec.UNSET
    wms_tile_layers: Dataset | msgspec.UnsetType = msgspec.UNSET
    wmts_tile_layers: Dataset | msgspec.UnsetType = msgspec.UNSET
    yivi_attribute_groups: Dataset | msgspec.UnsetType = msgspec.UNSET

    # IMPORTING

    @overload
    @classmethod
    def from_raw_data(
        cls,
        raw_data: Mapping[str, str],
        *,
        needs_decode: Literal[True],
    ) -> Self: ...

    @overload
    @classmethod
    def from_raw_data(
        cls,
        raw_data: Mapping[str, list[ShallowJSONObject]],
        *,
        needs_decode: Literal[False] = False,
    ) -> Self: ...

    @classmethod
    def from_raw_data(
        cls,
        raw_data: Mapping[str, list[ShallowJSONObject] | str],
        *,
        needs_decode: bool = False,
    ) -> Self:
        """
        Create an instance from raw export data.

        The raw data is a mapping from resource (e.g. ``forms`` or ``formVariables``) to
        the raw JSON, either as bytestring or regular string. It will be decoded with
        msgspec. No UUID mapping is applied at this point yet.
        """
        if needs_decode:
            raw_data = {
                # str call for the type checker, it already is a string because of
                # needs_decode being True
                key: json_decoder.decode(str(value))
                for key, value in raw_data.items()
            }
        return msgspec.convert(raw_data, type=cls, strict=True, dec_hook=_dec_hook)

    @classmethod
    def from_zip(cls, file: str | PathLike[str] | ZipReadable) -> Self:
        with zipfile.ZipFile(file, "r") as zip_file:
            namelist = zip_file.namelist()
            raw_data = {
                resource: json_decoder.decode(zip_file.read(file_name))
                for resource in cls.__struct_encode_fields__
                if (file_name := f"{resource}.json") in namelist
            }
        return cls.from_raw_data(raw_data)

    # EXPORTING

    @overload
    def as_resources_mapping(self, *, encode: Literal[True]) -> Mapping[str, bytes]: ...

    @overload
    def as_resources_mapping(
        self, *, encode: Literal[False] = False
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
