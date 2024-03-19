import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Generic, Iterator, TypeVar, cast

import glom
from typing_extensions import override

from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.rendering import render_to_json
from openforms.contrib.zgw.service import (
    create_attachment_document,
    create_csv_document,
    create_report_document,
)
from openforms.formio.service import FormioData
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.exports import create_submission_export
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import Submission, SubmissionReport
from openforms.typing import JSONValue
from openforms.variables.service import get_static_variables
from openforms.variables.utils import get_variables_for_context

from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from .client import DocumentenClient, get_documents_client
from .models import ObjectsAPIRegistrationData
from .registration_variables import register as variables_registry
from .typing import (
    ConfigVersion,
    RegistrationOptions,
    RegistrationOptionsV1,
    RegistrationOptionsV2,
)

logger = logging.getLogger(__name__)


def _point_coordinate(value: Any) -> dict[str, Any] | object:
    if not value or not isinstance(value, list) or len(value) != 2:
        return SKIP
    return {"type": "Point", "coordinates": [value[0], value[1]]}


def build_options(
    plugin_options: RegistrationOptions, key_mapping: dict[str, str]
) -> dict[str, Any]:
    """
    Construct options from plugin options dict, allowing renaming of keys
    """
    options = {
        new_key: plugin_options[key_in_opts]
        for new_key, key_in_opts in key_mapping.items()
        if key_in_opts in plugin_options
    }
    return options


def register_submission_pdf(
    submission: Submission,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
) -> str:
    if not options["informatieobjecttype_submission_report"]:
        return ""

    submission_report = SubmissionReport.objects.get(submission=submission)
    submission_report_options = build_options(
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
    return report_document["url"]


def register_submission_csv(
    submission: Submission,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
) -> str:
    if not options.get("upload_submission_csv", False):
        return ""

    if not options["informatieobjecttype_submission_csv"]:
        return ""

    submission_csv_options = build_options(
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


def register_submission_attachments(
    submission: Submission,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
) -> list[str]:
    if not options["informatieobjecttype_attachment"]:
        return []

    attachment_urls: list[str] = []
    for attachment in submission.attachments:
        attachment_options = build_options(
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

    return attachment_urls


@contextmanager
def save_and_raise(registration_data: ObjectsAPIRegistrationData) -> Iterator[None]:
    """Save the registration data before raising a :class:`~openforms.registrations.exceptions.RegistrationFailed` exception."""

    try:
        yield
    except Exception as e:
        raise RegistrationFailed() from e
    finally:
        registration_data.save()


OptionsT = TypeVar(
    "OptionsT", RegistrationOptionsV1, RegistrationOptionsV2, contravariant=True
)


class ObjectsAPIRegistrationHandler(ABC, Generic[OptionsT]):
    """Provide the registration data to be sent to the Objects API.

    When registering a submission to the Objects API, the following happens:
    - Depending on the version (v1 or v2) of the options, the correct handler is instantiated.
    - ``save_registration_data`` is called, creating an instance of ``ObjectsAPIRegistrationData``.
    - ``get_object_data`` is called, and should make use of the saved registration data to build the payload
      to be sent to the Objects API.
    - Similarly, ``get_update_payment_status_data`` is called to get the PATCH payload to be sent
      to the Objects API.
    """

    def save_registration_data(
        self,
        submission: Submission,
        options: OptionsT,
    ) -> None:
        """Save the registration data.

        The creation of submission documents (report, attachment, csv) makes use of ZGW
        service functions (e.g. :func:`create_report_document`) and involves a mapping
        (and in some cases renaming) of variables which would otherwise not be
        accessible from here. For example, 'vertrouwelijkheidaanduiding' must be named
        'doc_vertrouwelijkheidaanduiding' because this is what the ZGW service functions
        use.
        """
        registration_data, _ = ObjectsAPIRegistrationData.objects.get_or_create(
            submission=submission
        )

        with get_documents_client() as documents_client, save_and_raise(
            registration_data
        ):
            if not registration_data.pdf_url:
                registration_data.pdf_url = register_submission_pdf(
                    submission, options, documents_client
                )

            if not registration_data.csv_url:
                registration_data.csv_url = register_submission_csv(
                    submission, options, documents_client
                )

            if not registration_data.attachment_urls:
                # TODO turn attachments into a dictionary when giving users more options than
                # just urls.
                registration_data.attachment_urls = register_submission_attachments(
                    submission, options, documents_client
                )

    @abstractmethod
    def get_object_data(
        self,
        submission: Submission,
        options: OptionsT,
    ) -> dict[str, Any]:
        """Get the object data payload to be sent to the Objects API."""
        pass

    @abstractmethod
    def get_update_payment_status_data(
        self, submission: Submission, options: OptionsT
    ) -> dict[str, Any] | None:
        pass


class ObjectsAPIV1Handler(ObjectsAPIRegistrationHandler[RegistrationOptionsV1]):
    """Provide the registration data for legacy (v1) registration options, using JSON templates."""

    @staticmethod
    def get_payment_context_data(submission: Submission) -> dict[str, Any]:
        return {
            "completed": submission.payment_user_has_paid,
            "amount": str(submission.payments.sum_amount()),
            "public_order_ids": submission.payments.get_completed_public_order_ids(),
        }

    @override
    def get_object_data(
        self,
        submission: Submission,
        options: RegistrationOptionsV1,
    ) -> dict[str, Any]:
        """Get the object data payload to be sent to the Objects API."""

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
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
                "uploaded_attachment_urls": registration_data.attachment_urls,
                "pdf_url": registration_data.pdf_url,
                "csv_url": registration_data.csv_url,
            },
        }

        object_mapping = {
            "record.geometry": FieldConf(
                RegistrationAttribute.locatie_coordinaat,
                transform=_point_coordinate,
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
    ) -> dict[str, Any] | None:

        if not options["payment_status_update_json"]:
            logger.warning(
                "Skipping payment status update because no template was configured."
            )
            return

        context = {
            "variables": get_variables_for_context(submission),
            "payment": self.get_payment_context_data(submission),
        }

        return render_to_json(options["payment_status_update_json"], context)


class ObjectsAPIV2Handler(ObjectsAPIRegistrationHandler[RegistrationOptionsV2]):

    @override
    def get_object_data(
        self, submission: Submission, options: RegistrationOptionsV2
    ) -> dict[str, Any]:
        state = submission.load_submission_value_variables_state()
        dynamic_values = state.get_data()
        static_values = state.static_data()
        static_values.update(
            {
                variable.key: variable.initial_value
                for variable in get_static_variables(
                    submission=submission,
                    variables_registry=variables_registry,
                )
            }
        )

        variables_values = FormioData(
            {
                **dynamic_values,
                **static_values,
            }
        ).data

        variables_mapping = options["variables_mapping"]
        record_data: dict[str, JSONValue] = {}

        for mapping in variables_mapping:
            variable_key = mapping["variable_key"]
            target_path = mapping["target_path"]

            # Type hint is wrong: currently some static variables are of type date/datetime
            value = cast(Any, variables_values[variable_key])

            # Comply with JSON Schema "format" specs:
            if isinstance(value, (datetime, date)):
                value = value.isoformat()

            glom.assign(record_data, glom.Path(*target_path), value, missing=dict)

        object_data = prepare_data_for_registration(
            record_data=record_data,
            objecttype=options["objecttype"],
            objecttype_version=options["objecttype_version"],
        )

        if geometry_variable_key := options.get("geometry_variable_key"):
            object_data["record"]["geometry"] = _point_coordinate(
                variables_values[geometry_variable_key]
            )

        return object_data

    @override
    def get_update_payment_status_data(
        self, submission: Submission, options: RegistrationOptionsV2
    ) -> None:
        # TODO
        return None


HANDLER_MAPPING: dict[ConfigVersion, ObjectsAPIRegistrationHandler[Any]] = {
    1: ObjectsAPIV1Handler(),
    2: ObjectsAPIV2Handler(),
}
