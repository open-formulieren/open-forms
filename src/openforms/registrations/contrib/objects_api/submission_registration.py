from typing import Any, Protocol, TypeVar, cast

from typing_extensions import override

from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.rendering import render_to_json
from openforms.contrib.zgw.service import (
    create_attachment_document,
    create_csv_document,
    create_report_document,
)
from openforms.submissions.exports import create_submission_export
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport
from openforms.variables.utils import get_variables_for_context

from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from .client import DocumentenClient, get_documents_client
from .typing import ConfigVersion, RegistrationOptionsV1, RegistrationOptionsV2

OptionsT = TypeVar(
    "OptionsT", RegistrationOptionsV1, RegistrationOptionsV2, contravariant=True
)


class ObjectsAPIRegistrationHandler(Protocol[OptionsT]):
    """Provide the registration data to be sent to the Objects API."""

    def get_object_data(
        self,
        submission: Submission,
        options: OptionsT,
    ) -> dict[str, Any]:
        """Get the object data payload to be sent to the Objects API."""
        ...

    def get_update_payment_status_data(
        self, submission: Submission, options: OptionsT
    ) -> dict[str, Any]: ...


class ObjectsAPIV1Handler(ObjectsAPIRegistrationHandler[RegistrationOptionsV1]):
    """Provide the registration data for legacy (v1) registration options, using JSON templates."""

    @staticmethod
    def _point_coordinate(value):
        if not value or not isinstance(value, list) or len(value) != 2:
            return SKIP
        return {"type": "Point", "coordinates": [value[0], value[1]]}

    @staticmethod
    def get_payment_context_data(submission: Submission) -> dict[str, Any]:
        return {
            "completed": submission.payment_user_has_paid,
            "amount": str(submission.payments.sum_amount()),
            "public_order_ids": submission.payments.get_completed_public_order_ids(),
        }

    @staticmethod
    def build_options(plugin_options: RegistrationOptionsV1, key_mapping: dict) -> dict:
        """
        Construct options from plugin options dict, allowing renaming of keys
        """
        options = {
            new_key: plugin_options[key_in_opts]
            for new_key, key_in_opts in key_mapping.items()
            if key_in_opts in plugin_options
        }
        return options

    def register_submission_csv(
        self,
        submission: Submission,
        options: RegistrationOptionsV1,
        documents_client: DocumentenClient,
    ) -> str:
        if not options.get("upload_submission_csv", False):
            return ""

        if not options["informatieobjecttype_submission_csv"]:
            return ""

        submission_csv_options = self.build_options(
            options,
            {
                "informatieobjecttype": "informatieobjecttype_submission_csv",
                "organisatie_rsin": "organisatie_rsin",
                "doc_vertrouwelijkheidaanduiding": "doc_vertrouwelijkheidaanduiding",
                "auteur": "auteur",
            },
        )
        qs = Submission.objects.filter(pk=submission.pk).select_related("auth_info")
        submission_csv = create_submission_export(qs).export("csv")  # type: ignore

        submission_csv_document = create_csv_document(
            client=documents_client,
            name=f"{submission.form.admin_name} (csv)",
            csv_data=submission_csv,
            options=submission_csv_options,
            language=submission.language_code,
        )

        return submission_csv_document["url"]

    @override
    def get_object_data(
        self,
        submission: Submission,
        options: RegistrationOptionsV1,
    ) -> dict[str, Any]:
        """Get the object data payload to be sent to the Objects API.

        The creation of submission documents (report, attachment, csv) makes use of ZGW
        service functions (e.g. :func:`create_report_document`) and involves a mapping
        (and in some cases renaming) of variables which would otherwise not be
        accessible from here. For example, 'vertrouwelijkheidaanduiding' must be named
        'doc_vertrouwelijkheidaanduiding' because this is what the ZGW service functions
        use.
        """

        # Prepare all documents to relate to the Objects API record
        with get_documents_client() as documents_client:
            # Create the document for the PDF summary
            submission_report = SubmissionReport.objects.get(submission=submission)
            submission_report_options = self.build_options(
                options,
                {
                    "informatieobjecttype": "informatieobjecttype_submission_report",
                    "organisatie_rsin": "organisatie_rsin",
                    "doc_vertrouwelijkheidaanduiding": "doc_vertrouwelijkheidaanduiding",
                },
            )

            report_document = create_report_document(
                client=documents_client,
                name=submission.form.admin_name,
                submission_report=submission_report,
                options=submission_report_options,
                language=submission_report.submission.language_code,
            )

            # Register the attachments
            # TODO turn attachments into dictionary when giving users more options then
            # just urls.
            attachment_urls: list[str] = []
            for attachment in submission.attachments:
                attachment_options = self.build_options(
                    options,
                    {
                        "informatieobjecttype": "informatieobjecttype_attachment",  # Different IOT than for the report
                        "organisatie_rsin": "organisatie_rsin",
                        "doc_vertrouwelijkheidaanduiding": "doc_vertrouwelijkheidaanduiding",
                    },
                )

                component_overwrites = {
                    "doc_vertrouwelijkheidaanduiding": attachment.doc_vertrouwelijkheidaanduiding,
                    "titel": attachment.titel,
                    "organisatie_rsin": attachment.bronorganisatie,
                    "informatieobjecttype": attachment.informatieobjecttype,
                }

                for key, value in component_overwrites.items():
                    if value:
                        attachment_options[key] = value

                attachment_document = create_attachment_document(
                    client=documents_client,
                    name=submission.form.admin_name,
                    submission_attachment=attachment,
                    options=attachment_options,
                    language=attachment.submission_step.submission.language_code,  # assume same as submission
                )
                attachment_urls.append(attachment_document["url"])

            # Create the CSV submission export, if requested.
            # If no CSV is being uploaded, then `assert csv_url == ""` applies.
            csv_url = self.register_submission_csv(
                submission, options, documents_client
            )

        context = {
            "_submission": submission,
            "productaanvraag_type": options["productaanvraag_type"],
            "payment": self.get_payment_context_data(submission),
            "variables": get_variables_for_context(submission),
            # Github issue #661, nested for namespacing note: other templates and context expose all submission
            # variables in the top level namespace, but that is due for refactor
            "submission": {
                "public_reference": submission.public_registration_reference,
                "kenmerk": str(submission.uuid),
                "language_code": submission.language_code,
                "uploaded_attachment_urls": attachment_urls,
                "pdf_url": report_document["url"],
                "csv_url": csv_url,
            },
        }

        object_mapping = {
            "record.geometry": FieldConf(
                RegistrationAttribute.locatie_coordinaat,
                transform=self._point_coordinate,
            ),
        }

        record_data = cast(
            dict[str, Any], render_to_json(options["content_json"], context)
        )
        object_data = prepare_data_for_registration(
            record_data=record_data,
            objecttype=options["objecttype"],
            objecttype_version=options["objecttype_version"],
        )
        object_data = apply_data_mapping(
            submission, object_mapping, REGISTRATION_ATTRIBUTE, object_data
        )
        return object_data

    @override
    def get_update_payment_status_data(
        self, submission: Submission, options: RegistrationOptionsV1
    ) -> dict[str, Any]:
        context = {
            "variables": get_variables_for_context(submission),
            "payment": self.get_payment_context_data(submission),
        }

        return render_to_json(options["payment_status_update_json"], context)


HANDLER_MAPPING: dict[ConfigVersion, ObjectsAPIRegistrationHandler[Any]] = {
    1: ObjectsAPIV1Handler(),
}
