import dataclasses
from collections.abc import Iterator

from django.db import models
from django.http import HttpResponse
from django.utils.timezone import make_naive

import tablib
from lxml import etree
from tablib.formats._json import serialize_objects_handler

from .models import Submission
from .rendering.base import Node
from .rendering.constants import RenderModes
from .rendering.renderer import Renderer


@dataclasses.dataclass
class FileType:
    extension: str
    content_type: str


class ExportFileTypes:
    CSV = FileType("csv", "text/csv")
    XLSX = FileType(
        "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    JSON = FileType("json", "application/json")
    XML = FileType("xml", "text/xml")


def iter_submission_data_nodes(submission: Submission) -> Iterator[Node]:
    renderer = Renderer(submission, mode=RenderModes.export, as_html=False)
    for data_nodes in renderer.get_children():
        for node in data_nodes.get_children():
            if node.is_layout:
                continue
            yield node


def create_submission_export(queryset: models.QuerySet[Submission]) -> tablib.Dataset:
    """
    Turn a submissions queryset into a tablib dataset for export.

    .. note:: the queryset of submissions must all be of the same form!
    """
    # queryset *could* be empty
    if not queryset:
        return tablib.Dataset()

    first_submission = queryset[0]
    headers = ["Formuliernaam", "Inzendingdatum"]
    if first_submission.form.translation_enabled:
        headers.append("Taalcode")

    for data_node in iter_submission_data_nodes(first_submission):
        if hasattr(data_node, "component"):
            headers.append(data_node.component["key"])
        elif hasattr(data_node, "variable"):
            headers.append(data_node.variable.key)

    data = tablib.Dataset(headers=headers)

    for submission in queryset:
        inzending_datum = (
            make_naive(submission.completed_on) if submission.completed_on else None
        )
        submission_data = [
            submission.form.admin_name,
            inzending_datum,
        ]
        if first_submission.form.translation_enabled:
            submission_data.append(submission.language_code)
        submission_data += [
            data_node.value for data_node in iter_submission_data_nodes(submission)
        ]
        data.append(submission_data)
    return data


def export_submissions(
    queryset: models.QuerySet[Submission], file_type: FileType
) -> HttpResponse:
    export_data = create_submission_export(queryset)
    filename = f"submissions_export.{file_type.extension}"

    response = HttpResponse(
        export_data.export(file_type.extension),
        content_type=file_type.content_type,
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


def _xml_basic_value(value) -> str:
    # let's re-use the JSON object serializer for dates, UUIDs, Decimals etc.
    return str(serialize_objects_handler(value))


def _xml_value(parent, value, wrap_single=False):
    if isinstance(value, list):
        for v in value:
            node = etree.SubElement(parent, "value")
            _xml_value(node, v)
    elif isinstance(value, dict):
        for k, v in value.items():
            node = etree.SubElement(parent, "value", name=k)
            _xml_value(node, v)
    else:
        if wrap_single:
            node = etree.SubElement(parent, "value")
        else:
            node = parent
        node.text = _xml_basic_value(value)


class XMLKeyValueExport:
    title = "xml"

    """
    example:

    <?xml version='1.0' encoding='utf8'?>
    <submissions>
        <submission>
            <field name="Formuliernaam">
              <value>Form 000</value>
            </field>
            <field name="Inzendingdatum">
              <value>2022-02-08T15:15:56.769534</value>
            </field>
            <field name="multi">
              <value>aaa</value>
              <value>bbb</value>
            </field>
    """

    @classmethod
    def export_set(cls, dset):
        root = etree.Element("submissions")
        for row in dset.dict:
            elem = etree.SubElement(root, "submission")
            for key, value in row.items():
                field = etree.SubElement(elem, "field", name=key)
                _xml_value(field, value, wrap_single=True)

        return etree.tostring(
            root, xml_declaration=True, encoding="utf8", pretty_print=True
        )
