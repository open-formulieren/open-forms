import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Iterator, Literal, TypeVar, cast, override

from django.db.models import F

import glom
from glom import PathAccessError

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.clients import (
    CatalogiClient,
    DocumentenClient,
    get_catalogi_client,
    get_documents_client,
)
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.rendering import render_to_json
from openforms.contrib.zgw.service import (
    DocumentOptions,
    create_attachment_document,
    create_csv_document,
    create_report_document,
)
from openforms.formio.service import FormioData
from openforms.formio.typing import Component
from openforms.payments.constants import PaymentStatus
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.exports import create_submission_export
from openforms.submissions.mapping import SKIP, FieldConf, apply_data_mapping
from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
)
from openforms.typing import JSONObject
from openforms.utils.date import datetime_in_amsterdam
from openforms.variables.constants import FormVariableSources
from openforms.variables.service import get_static_variables
from openforms.variables.utils import get_variables_for_context

from ...constants import REGISTRATION_ATTRIBUTE, RegistrationAttribute
from .models import ObjectsAPIRegistrationData, ObjectsAPISubmissionAttachment
from .registration_variables import (
    PAYMENT_VARIABLE_NAMES,
    get_cosign_value,
    register as variables_registry,
)
from .typing import (
    ConfigVersion,
    ObjecttypeVariableMapping,
    RegistrationOptions,
    RegistrationOptionsV1,
    RegistrationOptionsV2,
)

logger = logging.getLogger(__name__)


def _point_coordinate(value: Any) -> dict[str, Any] | object:
    if not isinstance(value, list) or len(value) != 2:
        return SKIP
    return {"type": "Point", "coordinates": [value[0], value[1]]}


def _resolve_documenttype(
    field: Literal["submission_report", "submission_csv", "attachment"],
    options: RegistrationOptions,
    submission: Submission,
    catalogi_client: CatalogiClient,
) -> str:
    """
    Given the registration options, resolve the documenttype URL to use.

    :arg field: for which kind of upload the document type must be resolved.
    :return: the resolved document type URL, if any. Empty string means that the upload
      should be skipped.
    """
    catalogue = options.get("catalogue")
    match field:
        case "submission_report":
            description = options["iot_submission_report"]
            url_ref = options.get("informatieobjecttype_submission_report", "")
        case "submission_csv":
            description = options["iot_submission_csv"]
            url_ref = options.get("informatieobjecttype_submission_csv", "")
        case "attachment":
            description = options["iot_attachment"]
            url_ref = options.get("informatieobjecttype_attachment", "")
        case _:  # pragma: no cover
            raise RuntimeError(f"Unhandled field '{field}'.")

    # descriptions only work if a catalogue is provided to look up the document type
    # inside it
    if catalogue is None:
        return url_ref

    if not description:
        return url_ref

    # domain and rsin should not be empty, otherwise our validation is broken.
    assert catalogue["domain"] and catalogue["rsin"]
    assert submission.completed_on is not None

    version_valid_on = datetime_in_amsterdam(submission.completed_on).date()
    catalogus = catalogi_client.find_catalogus(**catalogue)
    if catalogus is None:
        raise RuntimeError(f"Could not resolve catalogue {catalogue}")

    versions = catalogi_client.find_informatieobjecttypen(
        catalogus=catalogus["url"],
        description=description,
        valid_on=version_valid_on,
    )
    if versions is None:
        raise RuntimeError(
            f"Could not find a document type with description '{description}' that is "
            f"valid on {version_valid_on.isoformat()}."
        )

    version = versions[0]
    return version["url"]


def register_submission_pdf(
    submission: Submission,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
    catalogi_client: CatalogiClient,
) -> str:
    document_type = _resolve_documenttype(
        "submission_report", options, submission, catalogi_client
    )
    if not document_type:
        return ""

    submission_report = SubmissionReport.objects.get(submission=submission)
    report_document = create_report_document(
        client=documents_client,
        name=submission.form.admin_name,
        submission_report=submission_report,
        options={
            "informatieobjecttype": document_type,
            "organisatie_rsin": options.get("organisatie_rsin", ""),
        },
        language=submission_report.submission.language_code,
    )
    return report_document["url"]


def register_submission_csv(
    submission: Submission,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
    catalogi_client: CatalogiClient,
) -> str:
    if not options.get("upload_submission_csv", False):
        return ""

    document_type = _resolve_documenttype(
        "submission_csv", options, submission, catalogi_client
    )
    if not document_type:
        return ""

    qs = Submission.objects.filter(pk=submission.pk).select_related("auth_info")
    submission_csv = create_submission_export(qs).export("csv")

    submission_csv_document = create_csv_document(
        client=documents_client,
        name=f"{submission.form.admin_name} (csv)",
        csv_data=submission_csv,
        options={
            "informatieobjecttype": document_type,
            "organisatie_rsin": options.get("organisatie_rsin", ""),
        },
        language=submission.language_code,
    )

    return submission_csv_document["url"]


def register_submission_attachment(
    submission: Submission,
    attachment: SubmissionFileAttachment,
    options: RegistrationOptions,
    documents_client: DocumentenClient,
    catalogi_client: CatalogiClient,
) -> str:
    default_document_type = _resolve_documenttype(
        "attachment", options, submission, catalogi_client
    )
    assert default_document_type, "Registration should have been skipped"

    # registration for submissions that aren't completed does not make sense and the
    # assert helps with type narrowing
    assert submission.completed_on is not None

    document_options: DocumentOptions = {
        "informatieobjecttype": default_document_type,
        "organisatie_rsin": options.get("organisatie_rsin", ""),
        "ontvangstdatum": datetime_in_amsterdam(submission.completed_on)
        .date()
        .isoformat(),
    }

    # apply overrides from the attachment itself, if set
    if va := attachment.doc_vertrouwelijkheidaanduiding:
        document_options["doc_vertrouwelijkheidaanduiding"] = va
    if title := attachment.titel:
        document_options["titel"] = title
    if rsin := attachment.bronorganisatie:
        document_options["organisatie_rsin"] = rsin
    # TODO convert this to catalogue + description mechanism too! See #4267
    if document_type := attachment.informatieobjecttype:
        document_options["informatieobjecttype"] = document_type

    attachment_document = create_attachment_document(
        client=documents_client,
        name=submission.form.admin_name,
        submission_attachment=attachment,
        options=document_options,
        language=attachment.submission_step.submission.language_code,  # assume same as submission
    )

    return attachment_document["url"]


@contextmanager
def save_and_raise(
    registration_data: ObjectsAPIRegistrationData,
    submission_attachments: list[ObjectsAPISubmissionAttachment],
) -> Iterator[None]:
    """Save the registration data before raising a :class:`~openforms.registrations.exceptions.RegistrationFailed` exception."""

    try:
        yield
    except Exception as e:
        raise RegistrationFailed() from e
    finally:
        registration_data.save()
        ObjectsAPISubmissionAttachment.objects.bulk_create(submission_attachments)


OptionsT = TypeVar(
    "OptionsT", RegistrationOptionsV1, RegistrationOptionsV2, contravariant=True
)


class ObjectsAPIRegistrationHandler(ABC, Generic[OptionsT]):
    """Provide the registration data to be sent to the Objects API.

    When registering a submission to the Objects API, the following happens:
    - Depending on the version (v1 or v2) of the options, the correct handler is instantiated.
    - ``save_registration_data`` is called, creating an instance of ``ObjectsAPIRegistrationData``.
    - ``get_record_data`` is called, and should make use of the saved registration data to build
      the record data to be sent to the Objects API.
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
        submission_attachments: list[ObjectsAPISubmissionAttachment] = []

        _is_attachment_document_type_configured = (
            options.get("catalogue") and options.get("iot_attachment")
        ) or options.get("informatieobjecttype_attachment")

        api_group = options["objects_api_group"]

        with (
            get_documents_client(api_group) as documents_client,
            get_catalogi_client(api_group) as catalogi_client,
            save_and_raise(registration_data, submission_attachments),
        ):
            if not registration_data.pdf_url:
                registration_data.pdf_url = register_submission_pdf(
                    submission,
                    options,
                    documents_client,
                    catalogi_client,
                )

            if not registration_data.csv_url:
                registration_data.csv_url = register_submission_csv(
                    submission,
                    options,
                    documents_client,
                    catalogi_client,
                )

            if _is_attachment_document_type_configured:
                existing = [
                    o.submission_file_attachment
                    for o in ObjectsAPISubmissionAttachment.objects.filter(
                        submission_file_attachment__submission_step__submission=submission
                    )
                ]

                for attachment in submission.attachments:
                    if attachment not in existing:
                        document_url = register_submission_attachment(
                            submission,
                            attachment,
                            options,
                            documents_client,
                            catalogi_client,
                        )
                        submission_attachments.append(
                            ObjectsAPISubmissionAttachment(
                                submission_file_attachment=attachment,
                                document_url=document_url,
                            )
                        )

    @abstractmethod
    def get_record_data(
        self,
        submission: Submission,
        options: OptionsT,
    ) -> dict[str, Any]:
        """Get the record data to be sent to the Objects API."""
        pass

    @abstractmethod
    def get_update_payment_status_data(
        self, submission: Submission, options: OptionsT
    ) -> dict[str, Any] | None:
        """Get the object data payload to be sent (either as a PATCH or PUT request) to the Objects API."""
        pass


class ObjectsAPIV1Handler(ObjectsAPIRegistrationHandler[RegistrationOptionsV1]):
    """Provide the registration data for legacy (v1) registration options, using JSON templates."""

    @staticmethod
    def get_payment_context_data(submission: Submission) -> dict[str, Any]:
        price = submission.price
        amount = Decimal(price).quantize(Decimal("0.01")) if price is not None else 0
        return {
            "completed": submission.payment_user_has_paid,
            "amount": str(amount),
            "public_order_ids": submission.payments.get_completed_public_order_ids(),
            "provider_payment_ids": list(
                submission.payments.filter(
                    status__in=(PaymentStatus.registered, PaymentStatus.completed)
                ).values_list("provider_payment_id", flat=True)
            ),
        }

    @staticmethod
    def get_cosign_context_data(
        submission: Submission,
    ) -> dict[str, str | datetime] | None:
        if not submission.cosign_complete:
            return None
        else:
            # date can be missing on existing submissions, so fallback to an empty string
            date = (
                datetime.fromisoformat(submission.co_sign_data["cosign_date"])
                if "cosign_date" in submission.co_sign_data
                else ""
            )
            return {
                "bsn": get_cosign_value(submission, AuthAttribute.bsn),
                "kvk": get_cosign_value(submission, AuthAttribute.kvk),
                "pseudo": get_cosign_value(submission, AuthAttribute.pseudo),
                "date": date,
            }

    @override
    def get_record_data(
        self,
        submission: Submission,
        options: RegistrationOptionsV1,
    ) -> dict[str, Any]:
        """Get the record data to be sent to the Objects API."""

        # help the type checker a little, our 'apply_defaults_to' does some heavy
        # lifting.
        assert "productaanvraag_type" in options
        assert "content_json" in options

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        objects_api_attachments = ObjectsAPISubmissionAttachment.objects.filter(
            submission_file_attachment__submission_step__submission=submission
        )

        context = {
            "_submission": submission,
            "productaanvraag_type": options["productaanvraag_type"],
            "payment": self.get_payment_context_data(submission),
            "cosign_data": self.get_cosign_context_data(submission),
            "variables": get_variables_for_context(submission),
            # Github issue #661, nested for namespacing note: other templates and context expose all submission
            # variables in the top level namespace, but that is due for refactor
            "submission": {
                "public_reference": submission.public_registration_reference,
                "kenmerk": str(submission.uuid),
                "language_code": submission.language_code,
                "uploaded_attachment_urls": [
                    attachment.document_url for attachment in objects_api_attachments
                ],
                "pdf_url": registration_data.pdf_url,
                "csv_url": registration_data.csv_url,
            },
        }

        object_mapping = {
            "geometry": FieldConf(
                RegistrationAttribute.locatie_coordinaat,
                transform=_point_coordinate,
            ),
        }

        data = cast(dict[str, Any], render_to_json(options["content_json"], context))
        record_data = prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )
        record_data = apply_data_mapping(
            submission, object_mapping, REGISTRATION_ATTRIBUTE, record_data
        )
        return record_data

    @override
    def get_update_payment_status_data(
        self, submission: Submission, options: RegistrationOptionsV1
    ) -> dict[str, Any] | None:
        assert "payment_status_update_json" in options

        if not options["payment_status_update_json"]:
            logger.warning(
                "Skipping payment status update because no template was configured."
            )
            return

        context = {
            "variables": get_variables_for_context(submission),
            "payment": self.get_payment_context_data(submission),
        }

        data = cast(
            dict[str, Any],
            render_to_json(options["payment_status_update_json"], context),
        )

        return prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )


class ObjectsAPIV2Handler(ObjectsAPIRegistrationHandler[RegistrationOptionsV2]):

    @staticmethod
    def _get_data(
        variables_values: FormioData, variables_mapping: list[ObjecttypeVariableMapping]
    ) -> JSONObject:
        record_data: JSONObject = {}

        for mapping in variables_mapping:
            variable_key = mapping["variable_key"]
            if variable_key not in variables_values:
                # This should only happen for payment status update,
                # where only a subset of the variables are updated.
                continue
            target_path = mapping["target_path"]

            # Type hint is wrong: currently some static variables are of type date/datetime
            value = cast(Any, variables_values[variable_key])

            # Comply with JSON Schema "format" specs:
            if isinstance(value, (datetime, date)):
                value = value.isoformat()

            glom.assign(record_data, glom.Path(*target_path), value, missing=dict)

        return record_data

    @staticmethod
    def _process_value(value: Any, component: Component) -> Any:
        match component:
            # multiple files - return an array
            case {"type": "file", "multiple": True}:
                assert isinstance(value, list)
                return value
            # single file - return only one element
            case {"type": "file"}:
                assert isinstance(value, list)
                return value[0] if value else ""

            case {"type": "map"}:
                # Currently we only support Point coordinates
                return _point_coordinate(value)
            case _:
                return value

    @override
    def get_record_data(
        self, submission: Submission, options: RegistrationOptionsV2
    ) -> dict[str, Any]:

        state = submission.load_submission_value_variables_state()
        dynamic_values = FormioData(state.get_data())

        # For every file upload component, we alter the value of the variable to be
        # the Document API URL(s).
        objects_api_attachments = ObjectsAPISubmissionAttachment.objects.filter(
            submission_file_attachment__submission_variable__submission=submission
        ).annotate(
            variable_key=F("submission_file_attachment__submission_variable__key")
        )

        urls_map: defaultdict[str, list[str]] = defaultdict(list)
        for o in objects_api_attachments:
            urls_map[o.variable_key].append(o.document_url)  # type: ignore

        for key, variable in state.variables.items():
            try:
                submission_value = dynamic_values[key]
            except PathAccessError:
                continue

            # special casing documents - we transform the formio file upload data into
            # the api resource URLs for the uploaded documents in the Documens API.
            #
            # Normalizing to string/array of strings is done in the _process_value
            # method.
            if key in urls_map:
                submission_value = urls_map[key]

            # look up the component used (if relevant) to perform any required
            # pre-processing.
            if (variable.form_variable.source) == FormVariableSources.component:
                component = variable.form_variable.form_definition.configuration_wrapper.component_map[
                    key
                ]
                # update the value after processing to make it objects-API suitable
                dynamic_values[key] = self._process_value(submission_value, component)

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

        variables_values = FormioData({**dynamic_values, **static_values})
        variables_mapping = options["variables_mapping"]
        data = self._get_data(variables_values, variables_mapping)

        record_data = prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )

        if geometry_variable_key := options.get("geometry_variable_key"):
            record_data["geometry"] = variables_values[geometry_variable_key]

        return record_data

    @override
    def get_update_payment_status_data(
        self, submission: Submission, options: RegistrationOptionsV2
    ) -> dict[str, Any]:

        values = {
            variable.key: variable.initial_value
            for variable in get_static_variables(
                submission=submission,
                variables_registry=variables_registry,
            )
            if variable.key in PAYMENT_VARIABLE_NAMES
        }

        variables_values = FormioData(values)
        variables_mapping = options["variables_mapping"]
        data = self._get_data(variables_values, variables_mapping)

        record_data = prepare_data_for_registration(
            data=data,
            objecttype_version=options["objecttype_version"],
        )

        return record_data


HANDLER_MAPPING: dict[ConfigVersion, ObjectsAPIRegistrationHandler[Any]] = {
    1: ObjectsAPIV1Handler(),
    2: ObjectsAPIV2Handler(),
}
