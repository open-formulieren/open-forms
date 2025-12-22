import uuid
from collections import defaultdict
from collections.abc import (
    Collection,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import groupby

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import requests
import structlog
from django_yubin.models import Message
from furl import furl
from json_logic.typing import JSON
from lxml import etree
from requests.exceptions import RequestException
from rest_framework import serializers
from simple_certmanager.models import Certificate
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.config.models import GlobalConfiguration, MapWMSTileLayer
from openforms.contrib.brk.service import check_brk_config_for_addressNL
from openforms.contrib.kadaster.service import check_bag_config_for_address_fields
from openforms.contrib.reference_lists.client import (
    ReferenceListsClient,
    Table,
    TableItem,
)
from openforms.formio.constants import DataSrcOptions
from openforms.formio.typing import Component
from openforms.formio.typing.map import Overlay
from openforms.forms.constants import LogicActionTypes
from openforms.forms.models import Form
from openforms.forms.models.form_registration_backend import FormRegistrationBackend
from openforms.forms.models.logic import FormLogic
from openforms.logging.models import TimelineLogProxy
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.contrib.customer_interactions.checks import (
    check_absent_user_variables_for_profile,
)
from openforms.prefill.contrib.family_members.service import (
    check_hc_config_for_family_members,
    check_unmatched_variables,
)
from openforms.prefill.contrib.stufbg.service import (
    check_stufbg_config_for_family_members,
)
from openforms.registrations.registry import register
from openforms.submissions.models.submission import Submission
from openforms.submissions.utils import get_filtered_submission_admin_url
from openforms.typing import StrOrPromise
from openforms.utils.json_logic.datastructures import InputVar
from openforms.utils.json_logic.introspection import introspect_json_logic
from openforms.utils.urls import build_absolute_uri
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.service import get_static_variables

logger = structlog.stdlib.get_logger(__name__)


@dataclass
class FailedEmail:
    submission_uuid: uuid.UUID
    event: str


@dataclass
class FailedRegistration:
    form_name: str
    failed_submissions_counter: int
    initial_failure_at: datetime
    last_failure_at: datetime
    admin_link: str
    has_errors: bool


@dataclass
class FailedPrefill:
    plugin_label: str
    form_names: list[str]
    submission_ids: list[str]
    initial_failure_at: datetime
    last_failure_at: datetime
    # whether an uncaught exception has happened or empty data was returned
    has_errors: bool

    @property
    def admin_link(self) -> str:
        content_type = ContentType.objects.get_for_model(Submission).id

        query_params = {
            "content_type": content_type,
            "object_id__in": ",".join(self.submission_ids),
            "extra_data__log_event__in": "prefill_retrieve_empty,prefill_retrieve_failure",
        }
        submissions_relative_admin_url = furl(
            reverse("admin:logging_timelinelogproxy_changelist")
        )
        submissions_relative_admin_url.add(query_params)

        return build_absolute_uri(submissions_relative_admin_url.url)

    @property
    def failed_submissions_counter(self) -> int:
        return len(self.submission_ids)


@dataclass
class BrokenConfiguration:
    config_name: StrOrPromise
    exception_message: StrOrPromise


@dataclass
class InvalidCertificate:
    id: int
    label: str
    error_message: str
    is_valid_pair: bool
    expiry_date: datetime | None = None

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:simple_certmanager_certificate_change",
            kwargs={"object_id": self.id},
        )

        return build_absolute_uri(form_relative_admin_url)


@dataclass
class InvalidRegistrationBackend:
    config_name: StrOrPromise
    exception_message: StrOrPromise
    form_name: str
    form_id: int

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:forms_form_change", kwargs={"object_id": self.form_id}
        )
        return build_absolute_uri(form_relative_admin_url)


@dataclass
class InvalidLogicRule:
    variable: str
    form_name: str
    form_id: int
    exception: bool = False
    rule_index: int = 0

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:forms_form_change", kwargs={"object_id": self.form_id}
        )

        return build_absolute_uri(form_relative_admin_url)


@dataclass
class ExpiringReferenceListsService:
    service: StrOrPromise
    tables: list[Table]
    table_items: list[TableItem]
    exception_message: StrOrPromise = ""

    @property
    def general_config_admin_link(self) -> str:
        general_config_admin_url = reverse("admin:config_globalconfiguration_change")
        return build_absolute_uri(general_config_admin_url)


@dataclass
class InvalidMapComponentOverlay:
    form_id: int
    form_name: str
    overlay_name: str
    component_name: str
    exception_message: StrOrPromise = ""

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:forms_form_change", kwargs={"object_id": self.form_id}
        )
        return build_absolute_uri(form_relative_admin_url)


@dataclass
class InvalidComponentConfiguration:
    form_id: int
    form_name: str
    component_key: str
    component_type: str
    exception_message: StrOrPromise

    @property
    def admin_link(self) -> str:
        form_relative_admin_url = reverse(
            "admin:forms_form_change", kwargs={"object_id": self.form_id}
        )
        return build_absolute_uri(form_relative_admin_url)


def collect_failed_emails(since: datetime) -> Sequence[FailedEmail]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__status=Message.STATUS_FAILED,
        extra_data__include_in_daily_digest=True,
    ).distinct("content_type", "extra_data__status", "extra_data__event")

    if not logs:
        return []

    failed_emails = [
        FailedEmail(
            submission_uuid=log.content_object.uuid, event=log.extra_data["event"]
        )
        for log in logs
    ]

    return failed_emails


def collect_failed_registrations(
    since: datetime,
) -> list[FailedRegistration]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event="registration_failure",
    ).order_by("timestamp")

    form_sorted_logs = sorted(logs, key=lambda x: x.content_object.form.admin_name)

    grouped_logs = groupby(form_sorted_logs, key=lambda log: log.content_object.form)

    failed_registrations = []
    for form, submission_logs in grouped_logs:
        logs = list(submission_logs)
        timestamps = []
        has_errors = False

        for log in logs:
            timestamps.append(log.timestamp)
            has_errors = has_errors or bool(log.extra_data.get("error"))

        failed_registrations.append(
            FailedRegistration(
                form_name=form.name,
                failed_submissions_counter=len(logs),
                initial_failure_at=min(timestamps),
                last_failure_at=max(timestamps),
                admin_link=get_filtered_submission_admin_url(
                    form.id, filter_retry=True, registration_time="24hAgo"
                ),
                has_errors=has_errors,
            )
        )

    return failed_registrations


def collect_failed_prefill_plugins(since: datetime) -> list[FailedPrefill]:
    logs = TimelineLogProxy.objects.filter(
        timestamp__gt=since,
        extra_data__log_event__in=[
            "prefill_retrieve_empty",
            "prefill_retrieve_failure",
        ],
    ).order_by("extra_data__plugin_label")

    grouped_logs = groupby(logs, key=lambda x: x.extra_data["plugin_label"])

    failed_prefill_plugins = []
    for prefill_plugin, submission_logs in grouped_logs:
        logs = list(submission_logs)

        timestamps = []
        forms = set()
        submission_ids = []
        has_errors = False

        for log in logs:
            timestamps.append(log.timestamp)
            forms.add(log.content_object.form.admin_name)
            submission_ids.append(log.object_id)
            has_errors = has_errors or bool(log.extra_data.get("error"))

        failed_prefill_plugins.append(
            FailedPrefill(
                plugin_label=prefill_plugin,
                form_names=sorted(forms),
                submission_ids=submission_ids,
                initial_failure_at=min(timestamps),
                last_failure_at=max(timestamps),
                has_errors=has_errors,
            )
        )

    return failed_prefill_plugins


def collect_broken_configurations() -> list[BrokenConfiguration]:
    check_brk_configuration = check_brk_config_for_addressNL()
    check_bag_configuration = check_bag_config_for_address_fields()
    check_hc_configuration = check_hc_config_for_family_members()
    check_stufbg_configuration = check_stufbg_config_for_family_members()
    check_variables_configuration = check_unmatched_variables()

    configurations = {
        _("BRK Client"): check_brk_configuration,
        _("BAG Client"): check_bag_configuration,
        _("Haal centraal Client"): check_hc_configuration,
        _("StUF-BG Client"): check_stufbg_configuration,
        _("User defined Variables"): check_variables_configuration,
    }

    broken_configurations = [
        BrokenConfiguration(config_name=name, exception_message=message)
        for name, message in configurations.items()
        if message
    ]

    return broken_configurations


def collect_invalid_certificates() -> list[InvalidCertificate]:
    today = timezone.now()
    error_messages = {
        "expired": _("expired"),
        "expiring": _("will expire soon"),
        "invalid": _("has invalid keypair"),
        "invalid_expired": _("invalid keypair, expired"),
        "invalid_expiring": _("invalid keypair, will expire soon"),
    }

    invalid_certs = []
    # filter only on the certificates that are used by services
    configured_certificates = Certificate.objects.filter(
        Q(soap_services_client__isnull=False)
        | Q(soap_services_server__isnull=False)
        | Q(service_client__isnull=False)
        | Q(service_server__isnull=False)
    )
    for cert in configured_certificates:
        error_message = ""
        is_valid_pair = cert.is_valid_key_pair()
        time_until_expiry = cert.expiry_date - today
        is_expired = time_until_expiry <= timedelta(days=0)
        no_longer_valid_in_two_weeks = time_until_expiry <= timedelta(days=14)

        match (no_longer_valid_in_two_weeks, is_valid_pair):
            case (True, True) | (True, None):
                error_message = (
                    error_messages["expired"]
                    if is_expired
                    else error_messages["expiring"]
                )

            case (False, False):
                error_message = error_messages["invalid"]

            case (True, False):
                error_message = (
                    error_messages["invalid_expired"]
                    if is_expired
                    else error_messages["invalid_expiring"]
                )

        if error_message:
            invalid_certs.append(
                InvalidCertificate(
                    id=cert.pk,
                    label=str(cert),
                    error_message=str(error_message),
                    is_valid_pair=is_valid_pair or is_valid_pair is None,
                    expiry_date=cert.expiry_date,
                )
            )

    return invalid_certs


def collect_invalid_registration_backends() -> list[InvalidRegistrationBackend]:
    registration_backends = (
        backend
        for backend in FormRegistrationBackend.objects.select_related("form").iterator()
        if backend.form.is_available
    )

    checked_plugins = set()
    invalid_registration_backends = []
    for registration_backend in registration_backends:
        form_name = registration_backend.form.admin_name
        form = registration_backend.form
        backend_options = registration_backend.options
        backend_type = registration_backend.backend
        plugin = register[backend_type]

        # errors in general configuration are more straightforward for the user,
        # so we show the exact ones
        plugin_cls = type(plugin)
        if plugin_cls not in checked_plugins:
            try:
                plugin.check_config()
            # we always raise an InvalidPluginConfiguration exception even when we have
            # errors like HTTPError
            except InvalidPluginConfiguration as e:
                invalid_registration_backends.append(
                    InvalidRegistrationBackend(
                        config_name=plugin.verbose_name,
                        exception_message=e.args[0],
                        form_name=form_name,
                        form_id=form.id,
                    )
                )
            checked_plugins.add(plugin_cls)

        # errors in the form level can be more detailed so here we want to show
        # a more general error and the link to the broken form to investigate
        serializer = plugin.configuration_options(
            data=backend_options,
            context={"validate_business_logic": True},
        )

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            invalid_registration_backends.append(
                InvalidRegistrationBackend(
                    config_name=plugin.verbose_name,
                    exception_message=_(
                        "Invalid registration backend configuration detected"
                    ),
                    form_name=form_name,
                    form_id=form.id,
                )
            )
        except Exception as exc:
            # Catch any unexpected error, because we don't want this function to crash
            invalid_registration_backends.append(
                InvalidRegistrationBackend(
                    config_name=plugin.verbose_name,
                    exception_message=_(
                        "Unexpected error appeared during the validation process: {exception}"
                    ).format(exception=exc),
                    form_name=form_name,
                    form_id=form.id,
                )
            )

    return invalid_registration_backends


def introspect_json_logic_wrapper(
    expression: JSON, form_name: str
) -> list[InputVar] | None:
    try:
        introspection_result = introspect_json_logic(expression).get_input_keys()
    except Exception as exc:
        logger.error(
            "logic_introspection_failure",
            form=form_name,
            expression=expression,
            exc_info=exc,
        )
        return None

    return introspection_result


def collect_invalid_logic_rules() -> list[InvalidLogicRule]:
    def _report(var_key: str = "", exception: bool = False, rule_index: int = 0):
        invalid_logic_rules.append(
            InvalidLogicRule(
                variable=var_key,
                form_name=form.admin_name,
                form_id=form.pk,
                exception=exception,
                rule_index=rule_index,
            )
        )

    forms = Form.objects.live().iterator()
    static_variables = {
        var.key: {"source": var.source, "type": var.data_type}
        for var in get_static_variables()
    }

    invalid_logic_rules = []
    for form in forms:
        form_variables = {
            form_variable.key: {
                "source": form_variable.source,
                "type": form_variable.data_type,
            }
            for form_variable in form.formvariable_set.all()  # pyright: ignore[reportAttributeAccessIssue]
        }

        all_keys = list(static_variables) + list(form_variables)

        form_logics = FormLogic.objects.filter(form=form)

        form_logics_vars = []
        for index, logic in enumerate(form_logics):
            logic_introspection_result = introspect_json_logic_wrapper(
                logic.json_logic_trigger, form.admin_name
            )

            if logic_introspection_result is None:
                _report(exception=True, rule_index=index + 1)

                # no need for checking actions since the logic rule is already broken
                continue

            form_logics_vars += logic_introspection_result

            for action in logic.actions:
                if action["action"]["type"] == LogicActionTypes.variable:
                    expression = action["action"]["value"]
                    action_introspection_result = introspect_json_logic_wrapper(
                        expression, form.admin_name
                    )

                    if action_introspection_result is None:
                        _report(exception=True, rule_index=index + 1)
                    else:
                        form_logics_vars.append(InputVar(key=action["variable"]))
                        form_logics_vars += action_introspection_result

        for var in set(form_logics_vars):
            # there is a variable with this exact key, it is a valid reference
            if var.key in all_keys:
                continue

            outer, *nested = var.key.split(".")

            # Before checking the type of the parent/outer bit, check if it exists in
            # the first place. It could also be that it's not a parent at all (nested is
            # empty), so that's a guaranteed broken reference too.
            if outer not in all_keys:
                _report(var.key)
                continue

            # Nested cannot be empty now - if it were, either the key exists as a var,
            # which is the first thing we checked above, or it doesn't exist as a var,
            # which is the second thing we checked above and errored out.
            assert nested

            # We can only check the outer bit of the variable, which must be a suitable
            # container type to be valid. Container types are objects and arrays, but
            # we only consider arrays as a valid type if the first bit of the nested
            # key is numeric, as this must refer to an array index.
            # E.g. foo.bar -> only objects are possible, but foo.3 -> objects and arrays
            # are possible (you could have a dict with the string "3" as key").
            expected_container_types = {FormVariableDataTypes.object}
            if nested[0].isnumeric():
                expected_container_types.add(FormVariableDataTypes.array)

            # Now, check that the type of the container variable is as expected. If the
            # variable does *not* have any of the container types, then it's a
            # guaranteed error since lookups inside primitives are not possible.
            parent_var = form_variables.get(outer) or static_variables.get(outer)
            assert parent_var is not None
            if parent_var["type"] not in expected_container_types:
                _report(var.key)
                continue

            # all the other situations - we cannot (yet) conclude anything meaningful,
            # so instead, log information for our own insight into (typical) usage/
            # constructions.
            logger.info(
                "detected_possible_invalid_variable_reference",
                variable=var.key,
                form=form.admin_name,
            )

    return invalid_logic_rules


def collect_expired_or_near_expiry_reference_lists_data() -> list[
    ExpiringReferenceListsService
]:
    config = GlobalConfiguration.get_solo()

    service_tables_items_mapping = defaultdict(lambda: {"tables": [], "items": []})
    live_forms = Form.objects.live()

    seen: set[tuple[str, str]] = set()  # (service_slug, table_code) tuples
    services_by_slug: dict[str, Service] = config.reference_lists_services.in_bulk(
        field_name="slug"
    )

    problems: list[ExpiringReferenceListsService] = []

    # check only the services that are used by active forms and by specific components
    for form in live_forms:
        components = form.iter_components()

        for component in components:
            if component["type"] not in ("selectboxes", "radio", "select"):
                continue
            if (
                component.get("openForms", {}).get("dataSrc")
                != DataSrcOptions.reference_lists
            ):
                continue

            assert "openForms" in component
            service_slug = component["openForms"].get("service", "")
            table_code = component["openForms"].get("code", "")

            # broken service reference
            if service_slug not in services_by_slug:
                seen_entry = (service_slug, "")
                if seen_entry in seen:
                    continue

                problems.append(
                    ExpiringReferenceListsService(
                        service=_("UNKNOWN"),
                        tables=[],
                        table_items=[],
                        exception_message=_(
                            "Service reference '{slug}' could not be resolved (used in form "
                            "{form})."
                        ).format(slug=service_slug, form=form.name),
                    )
                )
                seen.add(seen_entry)
                continue

            service = services_by_slug[service_slug]
            seen_entry = (service_slug, table_code)
            # don't report problems twice
            if seen_entry in seen:
                continue
            seen.add(seen_entry)

            service_label = service.label

            with build_client(service, client_factory=ReferenceListsClient) as client:
                try:
                    table = client.get_table(table_code)
                except RequestException as e:
                    problems.append(
                        ExpiringReferenceListsService(
                            service=service_label,
                            tables=[],
                            table_items=[],
                            exception_message=e.args[0] if e.args else "Unknown",
                        )
                    )
                    continue

                if table is None:
                    problems.append(
                        ExpiringReferenceListsService(
                            service=service_label,
                            tables=[],
                            table_items=[],
                            exception_message=_(
                                "Could not find table with code {code}"
                            ).format(code=table_code),
                        )
                    )
                    continue

                # expired or near expiry tables
                if table.is_expired or table.is_nearly_expired:
                    service_tables_items_mapping[service_label]["tables"].append(table)
                    # no point in further checking the items if the table as a whole is
                    # (nearly) expired
                    continue

                # expired or near expiry items
                try:
                    items = client.get_items_for_table_cached(code=table.code)
                except RequestException as e:
                    problems.append(
                        ExpiringReferenceListsService(
                            service=service_label,
                            tables=[],
                            table_items=[],
                            exception_message=e.args[0] if e.args else "Unknown",
                        )
                    )
                    continue

            # finally, check each item
            for item in items:
                if item.is_expired or item.is_nearly_expired:
                    service_tables_items_mapping[service_label]["items"].append(item)

    for service, data in service_tables_items_mapping.items():
        problems.append(
            ExpiringReferenceListsService(
                service=service,
                tables=data["tables"],
                table_items=data["items"],
            )
        )

    return problems


class WMS:
    """
    Helper to process WMS tile layer configuration.
    """

    _layers_for_wms_url: MutableMapping[str, set[str] | requests.RequestException]

    def __init__(self):
        self.session = requests.Session()
        self._layers_for_wms_url = {}

    def __enter__(self):
        self.session.__enter__()
        return self

    def __exit__(self, *args):
        self.session.__exit__(*args)

    def get_layer_names(self, wms_layer_url: str) -> Collection[str]:
        if self._layers_for_wms_url.get(wms_layer_url) is None:
            # populate the cache and do the expensive processing
            try:
                response = self.session.get(wms_layer_url)
                response.raise_for_status()
            except requests.RequestException as exc:
                self._layers_for_wms_url[wms_layer_url] = exc
            else:
                root = etree.fromstring(response.content)
                # Try with common wms standard namespace first (used in WMS 1.3.0)
                names = root.findall(
                    ".//wms:Layer/wms:Name",
                    namespaces={"wms": "http://www.opengis.net/wms"},
                    # Fallback to no namespace (for WMS 1.1.1)
                ) or root.findall(".//Layer/Name")

                self._layers_for_wms_url[wms_layer_url] = set(
                    element.text.strip() for element in names if element.text
                )

        cache_result = self._layers_for_wms_url[wms_layer_url]
        if isinstance(cache_result, requests.RequestException):
            raise cache_result
        return cache_result


def collect_invalid_map_component_overlays() -> list[InvalidMapComponentOverlay]:
    live_forms = Form.objects.live()
    wms_tile_layers_map: Mapping[str, str] = {
        str(uuid): str(url)
        for uuid, url in MapWMSTileLayer.objects.values_list("uuid", "url")
    }

    problems: list[InvalidMapComponentOverlay] = []

    def _iter_overlays() -> Iterator[tuple[Form, Component, Overlay]]:
        for form in live_forms:
            for component in form.iter_components(recursive=True):
                if component["type"] != "map":
                    continue
                if not (overlays := component.get("overlays", [])):
                    continue
                for overlay in overlays:
                    yield form, component, overlay

    with WMS() as wms_helper:
        for form, component, overlay in _iter_overlays():
            overlay_url = wms_tile_layers_map.get(overlay["uuid"])

            # Is the uuid connected to a known WMS tile layer
            if not overlay_url:
                problems.append(
                    InvalidMapComponentOverlay(
                        form_id=form.pk,
                        form_name=form.name,
                        overlay_name=overlay["label"],
                        component_name=component["key"],
                        exception_message=_("Invalid UUID"),
                    )
                )
                continue

            try:
                xml_layer_names = wms_helper.get_layer_names(overlay_url)
            except requests.RequestException:
                problems.append(
                    InvalidMapComponentOverlay(
                        form_id=form.pk,
                        form_name=form.name,
                        overlay_name=overlay["label"],
                        component_name=component["key"],
                        exception_message=_("Overlay url returned an error"),
                    )
                )
                continue

            # Check if all overlay layers are actually available in the WMS tile
            # layer. It could be that the WMS tile layer was updated, and that the
            # layer is no-longer available.
            missing_layers = set(overlay["layers"]) - set(xml_layer_names)
            if missing_layers:
                problems.append(
                    InvalidMapComponentOverlay(
                        form_id=form.pk,
                        form_name=form.name,
                        overlay_name=overlay["label"],
                        component_name=component["key"],
                        exception_message=_(
                            "Overlay uses unavailable layers: {layers}"
                        ).format(layers=", ".join(sorted(missing_layers))),
                    )
                )

    return problems


def collect_invalid_component_configuration() -> list[InvalidComponentConfiguration]:
    """
    Collects invalid formio component configurations for custom components.
    """
    invalid_component_configurations = check_absent_user_variables_for_profile()

    return invalid_component_configurations
