from __future__ import annotations

import re
from collections.abc import MutableMapping
from dataclasses import dataclass
from datetime import date, datetime
from functools import partial
from io import BytesIO
from typing import Any, override

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from json_logic.typing import Primitive

from openforms.emails.service import get_last_confirmation_email
from openforms.forms.models import FormVariable
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.base import BasePlugin, PreRegistrationResult
from openforms.registrations.constants import (
    REGISTRATION_ATTRIBUTE,
    RegistrationAttribute,
)
from openforms.submissions.mapping import (
    SKIP,
    FieldConf,
    apply_data_mapping,
    get_component,
    get_unmapped_data,
)
from openforms.submissions.models import (
    Submission,
    SubmissionReport,
)
from openforms.utils.pdf import convert_html_to_pdf
from openforms.variables.constants import FormVariableSources
from openforms.variables.service import get_static_variables
from stuf.stuf_zds.client import (
    NoServiceConfigured,
    PaymentStatus,
    ZaakOptions,
    get_client,
)
from stuf.stuf_zds.models import StufZDSConfig

from ...exceptions import RegistrationFailed
from ...registry import register
from ...utils import execute_unless_result_exists
from .options import ZaakOptionsSerializer
from .registration_variables import register as variables_registry
from .typing import RegistrationOptions
from .utils import flatten_data

logger = structlog.stdlib.get_logger(__name__)

PLUGIN_IDENTIFIER = "stuf-zds-create-zaak"


@dataclass
class PartialDate:
    year: int | None = None
    month: int | None = None
    day: int | None = None

    @property
    def indicator(self):
        if self.year and self.month and self.day:
            return "V"
        elif self.year and self.month:
            return "D"
        elif self.year:
            return "M"
        else:
            return "J"

    @property
    def value(self):
        if self.year and self.month and self.day:
            return f"{self.year:04}{self.month:02}{self.day:02}"
        elif self.year and self.month:
            return f"{self.year:04}{self.month:02}"
        elif self.year:
            return f"{self.year:04}"
        else:
            return ""

    def __str__(self):
        return self.value

    @classmethod
    def parse(cls, partial_date: str | date | datetime):
        """Parse a partial date or a date/datetime object

        Supports the following partial dates:
            2000-01-01
            2000-1-1
            2000-01
            2000-1
            2000
        """

        def _safe_int(num):
            try:
                num = int(num)
                if num == 0:
                    return None
                else:
                    return num
            except TypeError:
                return None

        match partial_date:
            case date() | datetime():
                return cls(partial_date.year, partial_date.month, partial_date.day)
            case str():
                m = re.match(r"^(0|\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?$", partial_date)
                if not m:
                    return cls()
                else:
                    return cls(
                        _safe_int(m.group(1)),
                        _safe_int(m.group(2)),
                        _safe_int(m.group(3)),
                    )
            case _:
                return cls()


def _gender_choices(value):
    """
    Convert value to uppercase, take only the first character and see if it's
    valid for StUF 'geslachtsaanduiding'.
    """
    value = str(value).upper()[:1]
    if value not in ["M", "V", "O"]:
        return SKIP
    return value


def _prepare_value(value: Any):
    match value:
        case bool():
            return "true" if value else "false"
        case float():
            return str(value)
        case _:
            return value


def _get_extra_payment_variables(submission: Submission, options: RegistrationOptions):
    key_mapping = {
        mapping["form_variable"]: mapping["stuf_name"]
        for mapping in options.get("payment_status_update_mapping", [])
    }
    return {
        key_mapping[variable.key]: _prepare_value(variable.initial_value)
        for variable in get_static_variables(
            submission=submission,
            variables_registry=variables_registry,
        )
        if variable.key
        in [
            "payment_completed",
            "payment_amount",
            "payment_public_order_ids",
            "provider_payment_ids",
        ]
        and variable.key in key_mapping
    }


@register(PLUGIN_IDENTIFIER)
class StufZDSRegistration(BasePlugin[RegistrationOptions]):
    verbose_name = _("StUF-ZDS")
    configuration_options = ZaakOptionsSerializer

    zaak_mapping = {
        # Initiator
        # Medewerker
        "initiator.medewerker_nummer": RegistrationAttribute.initiator_medewerker_nummer,
        # Natuurlijk Persoon
        "initiator.voorletters": RegistrationAttribute.initiator_voorletters,
        "initiator.voornamen": RegistrationAttribute.initiator_voornamen,
        "initiator.voorvoegselGeslachtsnaam": RegistrationAttribute.initiator_tussenvoegsel,
        "initiator.geslachtsnaam": RegistrationAttribute.initiator_geslachtsnaam,
        "initiator.geslachtsaanduiding": FieldConf(
            RegistrationAttribute.initiator_geslachtsaanduiding,
            transform=_gender_choices,
        ),
        "initiator.geboortedatum": FieldConf(
            RegistrationAttribute.initiator_geboortedatum, transform=PartialDate.parse
        ),
        # "initiator.aanschrijfwijze": FieldConf(RegistrationAttribute.initiator_aanschrijfwijze),
        # Verblijfsadres for both Natuurlijk Persoon and Vestiging
        "initiator.verblijfsadres.woonplaatsNaam": RegistrationAttribute.initiator_woonplaats,
        "initiator.verblijfsadres.postcode": RegistrationAttribute.initiator_postcode,
        "initiator.verblijfsadres.straatnaam": RegistrationAttribute.initiator_straat,
        "initiator.verblijfsadres.huisnummer": RegistrationAttribute.initiator_huisnummer,
        "initiator.verblijfsadres.huisletter": RegistrationAttribute.initiator_huisletter,
        "initiator.verblijfsadres.huisnummertoevoeging": RegistrationAttribute.initiator_huisnummer_toevoeging,
        # heeftAlsAanspreekpunt for Natuurlijk Persoon
        "initiator.contactpersoonNaam": RegistrationAttribute.initiator_contactpersoonNaam,
        "initiator.telefoonnummer": RegistrationAttribute.initiator_telefoonnummer,
        "initiator.emailadres": RegistrationAttribute.initiator_emailadres,
        # Vestiging
        "initiator.vestigingsNummer": RegistrationAttribute.initiator_vestigingsnummer,
        "initiator.handelsnaam": RegistrationAttribute.initiator_handelsnaam,
        # Identifiers
        "initiator.bsn": FieldConf(submission_auth_info_attribute="bsn"),
        "initiator.kvk": FieldConf(submission_auth_info_attribute="kvk"),
        # Location
        "locatie": FieldConf(RegistrationAttribute.locatie_coordinaat),
        # Family members
        "partners": RegistrationAttribute.partners,
        "children": RegistrationAttribute.children,
    }

    def pre_register_submission(
        self, submission: Submission, options: RegistrationOptions
    ) -> PreRegistrationResult:
        zaak_options: ZaakOptions = {
            **options,
            "omschrijving": submission.form.admin_name,
        }
        with get_client(options=zaak_options) as client:
            # obtain a zaaknummer & save it - first, check if we have an intermediate result
            # from earlier attempts. if we do, do not generate a new number
            zaak_id = execute_unless_result_exists(
                client.create_zaak_identificatie,
                submission,
                "intermediate.zaaknummer",
                default="",
            )

        return PreRegistrationResult(reference=zaak_id)

    def get_extra_data(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict[str, Any]:
        data = get_unmapped_data(submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE)
        payment_extra = _get_extra_payment_variables(submission, options)
        return {**data, **payment_extra}

    def process_partners(
        self,
        submission: Submission,
        zaak_data: MutableMapping[str, Any],
        extra_data: dict[str, Any],
    ) -> None:
        # register as zaakbetrokkene
        if RegistrationAttribute.partners in zaak_data:
            component = get_component(
                submission,
                RegistrationAttribute.partners,
                REGISTRATION_ATTRIBUTE,
            )

            assert component is not None
            assert component["type"] == "partners"

            fm_immutable_variable = FormVariable.objects.filter(
                source=FormVariableSources.user_defined,
                form=submission.form,
                prefill_plugin="family_members",
                prefill_options__mutable_data_form_variable=component["key"],
            ).first()

            if fm_immutable_variable:
                if fm_immutable_variable.key in extra_data:
                    del extra_data[fm_immutable_variable.key]

                # xml file generation depends on whether the variable was prefilled or not
                # (authentiek)
                state = submission.load_submission_value_variables_state()
                submission_variable = state.get_variable(fm_immutable_variable.key)

                # update the zaak data with the information needed for the xml request
                for partner in zaak_data[RegistrationAttribute.partners]:
                    partner.update(
                        {
                            "dateOfBirth": partner["dateOfBirth"].strftime("%Y%m%d"),
                            "prefilled": bool(submission_variable),
                        }
                    )
                    del partner["dateOfBirthPrecision"]
        # register as extraElementen
        else:
            variables = FormVariable.objects.filter(
                source=FormVariableSources.user_defined,
                form=submission.form,
                prefill_plugin="family_members",
                prefill_options__type="partners",
            )

            for variable in variables:
                from_key, to_key = (
                    variable.key,
                    variable.prefill_options["mutable_data_form_variable"],
                )
                value = extra_data[from_key]
                for item in value:
                    del item["dateOfBirthPrecision"]

                    item["dateOfBirth"] = item["dateOfBirth"].isoformat()

                extra_data[to_key] = value
                del extra_data[from_key]

    def process_children(
        self,
        submission: Submission,
        zaak_data: MutableMapping[str, Any],
        extra_data: dict[str, Any],
    ) -> None:
        non_related_properties = {
            "dateOfBirthPrecision",
            "__id",
            "__addedManually",
            "selected",
        }

        # register as zaakbetrokkene
        if RegistrationAttribute.children in zaak_data:
            component = get_component(
                submission,
                RegistrationAttribute.children,
                REGISTRATION_ATTRIBUTE,
            )

            assert component is not None
            assert component["type"] == "children"

            fm_immutable_variable = FormVariable.objects.filter(
                source=FormVariableSources.user_defined,
                form=submission.form,
                prefill_plugin="family_members",
                prefill_options__type="children",
                prefill_options__mutable_data_form_variable=component["key"],
            ).first()

            if fm_immutable_variable:
                if fm_immutable_variable.key in extra_data:
                    del extra_data[fm_immutable_variable.key]

                # update the zaak data with the information needed for the xml request
                updated = []
                for child in zaak_data[RegistrationAttribute.children]:
                    # keep only the selected ones or all of them if selection is not allowed
                    if child.get("selected") in (None, True):
                        child.update(
                            {
                                "dateOfBirth": child["dateOfBirth"].strftime("%Y%m%d"),
                                "prefilled": not child["__addedManually"],
                            }
                        )
                        # not useful for registration data
                        for property in non_related_properties:
                            child.pop(property, None)

                        updated.append(child)

                zaak_data[RegistrationAttribute.children] = updated

        # register as extraElementen
        else:
            variables = FormVariable.objects.filter(
                source=FormVariableSources.user_defined,
                form=submission.form,
                prefill_plugin="family_members",
                prefill_options__type="children",
            )

            for variable in variables:
                from_key, to_key = (
                    variable.key,
                    variable.prefill_options["mutable_data_form_variable"],
                )
                value = extra_data[to_key]

                updated = []
                for child in value:
                    if child.get("selected") in (None, True):
                        child["dateOfBirth"] = child["dateOfBirth"].isoformat()

                        for property in non_related_properties:
                            child.pop(property, None)

                        updated.append(child)

                value = updated
                extra_data[to_key] = value
                extra_data.pop(from_key, None)

    def register_submission(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict | None:
        """
        Register the submission by creating a ZAAK.

        Any attachments and the submission report are added as ZAAK-DOCUMENTs.

        Because of the various calls needed to come to the "end-result", we store the
        intermediate results on the submission in the event retries are needed. This
        prevents Open Forms from reserving case numbers over and over again (for
        example). See #1183 for a reported issue about this.
        """
        zaak_options: ZaakOptions = {
            **options,
            "omschrijving": submission.form.admin_name,
            "cosigner": (
                cosign.signing_details["value"]
                if (cosign := submission.cosign_state).is_signed
                else ""
            ),
        }

        with get_client(options=zaak_options) as client:
            # Zaak ID reserved during the pre-registration phase
            zaak_id = submission.public_registration_reference

            zaak_data = apply_data_mapping(
                submission, self.zaak_mapping, REGISTRATION_ATTRIBUTE
            )
            if zaak_data.get("locatie"):
                component = get_component(
                    submission,
                    RegistrationAttribute.locatie_coordinaat,
                    REGISTRATION_ATTRIBUTE,
                )
                assert component is not None
                zaak_data["locatie"]["key"] = component["key"]

            extra_data = self.get_extra_data(submission, options)

            # mutate the zaak_data and the extra data for the family members components
            # according to the type of the registration we want to send (zaakbetrokkene
            # or extraElementen)
            self.process_partners(submission, zaak_data, extra_data)
            self.process_children(submission, zaak_data, extra_data)

            # The extraElement tag of StUF-ZDS expects primitive types
            extra_data = flatten_data(extra_data)

            assert submission.registration_result is not None
            if internal_reference := submission.registration_result.get(
                "temporary_internal_reference",
            ):
                zaak_data.update({"kenmerken": [internal_reference]})

            # Add medewerker to the data
            if submission.has_registrator:
                assert submission.registrator is not None
                zaak_data.update(
                    {
                        "registrator": {
                            "medewerker": {
                                "identificatie": submission.registrator.value
                            }
                        }
                    }
                )

            payment_status = (
                PaymentStatus.NVT
                if not submission.payment_required
                else (
                    PaymentStatus.FULL
                    if submission.payment_user_has_paid
                    else PaymentStatus.NOT_YET
                )
            )
            zaak_data.update({"betalings_indicatie": payment_status})

            execute_unless_result_exists(
                partial(
                    client.create_zaak,
                    zaak_id,
                    zaak_data,
                    LangInjection(submission, extra_data),
                ),
                submission,
                "intermediate.zaak_created",
                default=False,
                result=True,
            )

            doc_id = execute_unless_result_exists(
                client.create_document_identificatie,
                submission,
                "intermediate.document_nummers.pdf-report",
                default="",
            )
            submission_report = SubmissionReport.objects.get(submission=submission)
            execute_unless_result_exists(
                partial(
                    client.create_zaak_document, zaak_id, doc_id, submission_report
                ),
                submission,
                "intermediate.documents_created.pdf-report",
                default=False,
                result=True,
            )

            for attachment in submission.attachments:
                attachment_doc_id = execute_unless_result_exists(
                    client.create_document_identificatie,
                    submission,
                    f"intermediate.document_nummers.{attachment.id}",  # type: ignore
                    default="",
                )
                execute_unless_result_exists(
                    partial(
                        client.create_zaak_attachment,
                        zaak_id,
                        attachment_doc_id,
                        attachment,
                    ),
                    submission,
                    f"intermediate.documents_created.{attachment.id}",  # type: ignore
                    default=False,
                    result=True,
                )

        result = {
            "zaak": zaak_id,
            "document": doc_id,
        }
        return result

    def update_payment_status(
        self, submission: Submission, options: RegistrationOptions
    ):
        # The extraElement tag of StUF-ZDS expects primitive types
        extra_data = flatten_data(self.get_extra_data(submission, options))

        zaak_options: ZaakOptions = {
            **options,
            "omschrijving": submission.form.admin_name,
        }
        with get_client(zaak_options) as client:
            assert submission.registration_result is not None
            client.set_zaak_payment(
                submission.registration_result["zaak"],
                extra=LangInjection(submission, extra_data),
            )

    @override
    def get_variables(self) -> list[FormVariable]:
        return get_static_variables(variables_registry=variables_registry)

    def check_config(self):
        options: ZaakOptions = {
            "omschrijving": "MyForm",
            "zds_zaaktype_code": "test",
            "zds_zaaktype_omschrijving": "test",
            "zds_zaaktype_status_code": "test",
            "zds_zaaktype_status_omschrijving": "test",
            "zds_documenttype_omschrijving_inzending": "test",
        }  # type: ignore
        try:
            client = get_client(options)
        except NoServiceConfigured:
            raise InvalidPluginConfiguration(_("StufService not selected"))

        with client:
            try:
                client.check_config()
            except Exception as e:
                raise InvalidPluginConfiguration(
                    _("Could not connect: {exception}").format(exception=e)
                ) from e

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:stuf_zds_stufzdsconfig_change",
                    args=(StufZDSConfig.singleton_instance_id,),
                ),
            ),
        ]

    def update_registration_with_confirmation_email(
        self, submission: Submission, options: RegistrationOptions
    ) -> dict | None:
        logger.info(
            "update_registration_with_confirmation_email_started", options=options
        )

        if not submission.confirmation_email_sent:
            logger.info(
                "update_registration_with_confirmation_email_skipped",
                reason="no_confirmation_email_sent",
            )
            return None

        res = get_last_confirmation_email(submission)
        if res is None:
            logger.info(
                "update_registration_with_confirmation_email_aborted",
                reason="no_confirmation_email_found",
            )
            raise RegistrationFailed("Confirmation email was not found")
        html, message_id = res

        assert submission.registration_result

        zaak_options: ZaakOptions = {
            **options,
            "omschrijving": submission.form.admin_name,
            "cosigner": (
                cosign.signing_details["value"]
                if (cosign := submission.cosign_state).is_signed
                else ""
            ),
        }

        # Generate email
        content = BytesIO(convert_html_to_pdf(html))

        with get_client(options=zaak_options) as client:
            # Zaak ID reserved during the pre-registration phase
            zaak_id = submission.public_registration_reference

            doc_id = execute_unless_result_exists(
                client.create_document_identificatie,
                submission,
                f"intermediate.confirmation_emails.{message_id}.document_id",
            )
            execute_unless_result_exists(
                partial(
                    client.create_confirmation_email_attachment,
                    zaak_id,
                    doc_id,
                    content,
                ),
                submission,
                f"intermediate.confirmation_emails.{message_id}.document",
                default=False,
                result=True,
            )

        return submission.registration_result


class LangInjection:
    """Ensures the first extra element is the submission language
    and isn't shadowed by a form field with the same key"""

    def __init__(self, submission: Submission, extra_data: dict[str, Primitive]):
        self.submission = submission
        self.extra_data = extra_data

    def items(self):
        yield ("language_code", self.submission.language_code)
        yield from self.extra_data.items()
