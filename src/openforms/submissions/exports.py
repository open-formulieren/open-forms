import dataclasses

from django.http import FileResponse, HttpResponse
from django.utils.timezone import make_naive

import tablib
from lxml import etree
from tablib.formats._json import serialize_objects_handler

from .query import SubmissionQuerySet


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


def create_submission_export(queryset: SubmissionQuerySet) -> tablib.Dataset:
    headers = []
    for submission in queryset:
        headers += list(submission.get_merged_data().keys())
    headers = list(dict.fromkeys(headers))  # Remove duplicates
    data = tablib.Dataset(headers=["Formuliernaam", "Inzendingdatum"] + headers)
    for submission in queryset:
        inzending_datum = (
            make_naive(submission.completed_on) if submission.completed_on else None
        )
        submission_data = [
            submission.form.admin_name,
            inzending_datum,
        ]
        merged_data = submission.get_merged_data()
        for header in headers:
            submission_data.append(merged_data.get(header))
        data.append(submission_data)
    return data


def export_submissions(
    queryset: SubmissionQuerySet, file_type: FileType
) -> FileResponse:
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
