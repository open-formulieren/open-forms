"""
Provide tooling to migrate component and registration configurations.

Legacy configuration used document/case type URLs towards the Documenten API, Zaken API
and Objects API. New configuration patterns allow specifying pointers that can resolve
the URLs at runtime. The migration from legacy to new pattern needs to be done before
4.0 is deployed, which drops support for the legacy configuration.
"""

from collections.abc import Collection, Iterator, Mapping
from io import TextIOBase

from tabulate import tabulate
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.zgw.clients.catalogi import Catalogus, InformatieObjectType
from openforms.formio.typing import FileComponent
from openforms.forms.models import Form, FormDefinition, FormRegistrationBackend
from openforms.registrations.contrib.objects_api.config import (
    ObjectsAPIOptionsSerializer,
)
from openforms.registrations.contrib.objects_api.typing import (
    RegistrationOptions as ObjectsAPIRegistrationOptions,
)
from openforms.registrations.contrib.zgw_apis.options import ZaakOptionsSerializer
from openforms.registrations.contrib.zgw_apis.typing import (
    CatalogueOption,
    RegistrationOptions as ZGWRegistrationOptions,
)


class MigrationProblem(Exception):
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


class Migrator:
    def __init__(self, outfile: TextIOBase):
        self.outfile = outfile

    def migrate(self) -> None:
        formio_config_migrator = FormioConfigurationMigrator(outfile=self.outfile)
        registration_backend_migrator = RegistrationBackendMigrator(
            outfile=self.outfile
        )

        formio_config_migrator.migrate()
        registration_backend_migrator.migrate()

        if any(
            migrator.has_errors
            for migrator in (formio_config_migrator, registration_backend_migrator)
        ):
            raise MigrationProblem(
                "There are automatic migration problems, please analyze the output."
            )


def look_up_document_type(url: str) -> tuple[tuple[str, str], str]:
    service = Service.get_service(url=url)
    if service is None:
        raise MigrationProblem(f"No service configured (url: {url}).")

    client = build_client(service=service)
    response = client.get(url=url)
    if not response.ok:
        raise MigrationProblem(
            f"Documenttype URL response: HTTP {response.status_code} "
        )

    iot: InformatieObjectType = response.json()

    catalogus_url = iot["catalogus"]
    catalogus_response = client.get(url=catalogus_url)
    if not catalogus_response.ok:
        raise MigrationProblem(
            f"Catalogus URL response: HTTP {catalogus_response.status_code} "
        )

    catalogus: Catalogus = catalogus_response.json()

    return ((catalogus["domein"], catalogus["rsin"]), iot["omschrijving"])


class FormioConfigurationMigrator:
    processed_fds: set[int] = set()
    has_errors: bool = False

    def __init__(self, outfile: TextIOBase):
        self.outfile = outfile

    def migrate(self) -> None:
        """
        Migrate all forms in the environment.
        """
        qs = Form.objects.all()
        if not qs.exists():
            return

        def _run() -> Iterator[tuple[str, str, str]]:
            for form in qs.iterator():
                yield from _run_for_form(form)

        def _run_for_form(form: Form) -> Iterator[tuple[str, str, str]]:
            form_repr = f"{form.admin_name} (ID:  {form.pk})"
            step_details = self.migrate_form(form)
            if not step_details:
                yield (form_repr, "-", "-")
                return

            for i, (step_repr, component_details) in enumerate(step_details.items()):
                _form_repr = form_repr if i == 0 else ""
                if not component_details:
                    yield (_form_repr, step_repr, "-")
                    continue

                for j, (key, message) in enumerate(component_details.items()):
                    _step_repr = step_repr if j == 0 else ""
                    yield (_form_repr, _step_repr, f"{key}: {message}")

        self.outfile.write("...migrating file components in forms")
        self.outfile.write("")
        self.outfile.write(
            tabulate(
                _run(),
                headers=("Form", "Step", "Details"),
                maxcolwidths=[50, 50, 100],
            )
        )

    def migrate_form(self, form: Form) -> Mapping[str, Mapping[str, str]]:
        """
        Process all the form definitions used in a given form.
        """
        # track component details per step
        step_details: dict[str, Mapping[str, str]] = {}
        for form_definition in FormDefinition.objects.filter(formstep__form=form):
            if form_definition.pk in self.processed_fds:
                continue
            step_repr = f"{form_definition.admin_name} (ID: {form_definition.pk})"
            component_details = self.migrate_form_definition(form_definition)
            step_details[step_repr] = component_details
            self.processed_fds.add(form_definition.pk)
        return step_details

    def migrate_form_definition(
        self, form_definition: FormDefinition
    ) -> Mapping[str, str]:
        """
        Process all the file upload components in a form definition.

        If there are any component changes, the form definition is updated in the
        database.

        :return: Component keys that were updated.
        """
        # key: component key, value: detailed reporting information for the component
        component_details: dict[str, str] = {}
        config_wrapper = form_definition.configuration_wrapper
        # loop over all components in the form definition and process the file
        # components
        needs_save = False
        for component in config_wrapper:
            match component["type"]:
                case "file":
                    try:
                        changed = self.process_file_component(component)  # pyright: ignore[reportArgumentType]
                    except MigrationProblem as exc:
                        self.has_errors = True
                        component_details[component["key"]] = exc.message
                        continue
                case "editgrid":
                    # no special treatment needed, the child components are included in
                    # the config_wrapper already.
                    # TODO: validate/confirm this with a unit test!
                    continue
                case _:
                    continue

            if changed:
                needs_save = True
                component_details[component["key"]] = "Configuration update ok."

        if needs_save:
            form_definition.save()

        return component_details

    def process_file_component(self, component: FileComponent) -> bool:
        # no registration configuration at all - nothing to do
        if not (registration := component.get("registration")):
            return False

        # no legacy URL configured, do nothing
        if not (legacy_url := registration.get("informatieobjecttype")):
            return False

        # new format is already configured, do nothing
        document_type = registration.get("documentType", {})
        if (
            document_type.get("description")
            and (catalogue := document_type.get("catalogue"))
            and catalogue.get("domain")
            and catalogue.get("rsin")
        ):
            return False

        # look up the document type and fill out the catalogue + description
        ((domain, rsin), description) = look_up_document_type(legacy_url)

        if "registration" not in component:
            component["registration"] = {}
        component["registration"]["documentType"] = {
            "catalogue": {
                "domain": domain,
                "rsin": rsin,
            },
            "description": description,
        }

        return True


REGISTRATION_PLUGIN_IDS = (
    "zgw-create-zaak",
    "objects_api",
)


class RegistrationBackendMigrator:
    """
    Handle both ZGW APIs and Objects API.

    * Migrates the form-level registration plugin options.
    * Migrates the API group-level configuration.
    """

    has_errors: bool = False

    def __init__(self, outfile: TextIOBase):
        self.outfile = outfile

    def migrate(self):
        # TODO: report output, handle errors
        self.migrate_zgw_api_groups()
        self.migrate_objects_api_groups()

        forms = Form.objects.filter(
            registration_backends__backend__in=REGISTRATION_PLUGIN_IDS
        )
        if not forms.exists():
            return

        def _run() -> Iterator[tuple[str, str, str]]:
            for form in forms.iterator():
                form_repr = f"{form.admin_name} (ID:  {form.pk})"
                backends_output = self.migrate_form_registration_backends(form)
                if not backends_output:
                    yield (form_repr, "-", "-")
                for i, (backend, backend_details) in enumerate(backends_output.items()):
                    _form_repr = form_repr if i == 0 else ""
                    if not backend_details:
                        yield (_form_repr, backend, "-")
                        continue
                    for j, detail in enumerate(backend_details):
                        _backend = backend if j == 0 else ""
                        yield (_form_repr if j == 0 else "", _backend, detail)

        self.outfile.write("...migrating registration backend options")
        self.outfile.write("")
        self.outfile.write(
            tabulate(
                _run(),
                headers=("Form", "Registration backend", "Details"),
                maxcolwidths=[50, 50, 100],
            )
        )

    def migrate_zgw_api_groups(self):
        # there are no document type/case type fields at the API group level
        pass

    def migrate_objects_api_groups(self):
        groups = ObjectsAPIGroupConfig.objects.exclude(
            informatieobjecttype_submission_report="",
            informatieobjecttype_submission_csv="",
            informatieobjecttype_attachment="",
        )

        OLD_TO_NEW_FIELD_MAPPING: Mapping[str, str] = {
            "informatieobjecttype_submission_report": "iot_submission_report",
            "informatieobjecttype_submission_csv": "iot_submission_csv",
            "informatieobjecttype_attachment": "iot_attachment",
        }

        for group in groups:
            # if a catalogue is configured, assume it is valid - the reference was checked
            # at some point
            catalogue: tuple[str, str] | None = None
            if (domain := group.catalogue_domain) and (rsin := group.catalogue_rsin):
                catalogue = (domain, rsin)

            errors: list[MigrationProblem] = []
            fields_to_assign: dict[str, str] = {}

            # all references must resolve to objects within the same catalogue - if one
            # is already configured, all document types must resolve to the same one
            catalogues_seen: set[tuple[str, str]] = set()
            if catalogue is not None:
                catalogues_seen.add(catalogue)

            # check if there are fields that need to be migrated still, and validate
            # internal consistency
            for old_field, new_field in OLD_TO_NEW_FIELD_MAPPING.items():
                # if the reference is already configured, no need to bother with
                # migrating
                if getattr(group, new_field):
                    continue

                if not (legacy_url := getattr(group, old_field)):
                    continue

                try:
                    ((domain, rsin), description) = look_up_document_type(legacy_url)
                except MigrationProblem as exc:
                    errors.append(exc)
                    continue

                catalogues_seen.add((domain, rsin))
                fields_to_assign[new_field] = description

            # if we ran into resolution errors, now's the time to raise them
            if errors:
                self.has_errors = True
                raise ExceptionGroup(
                    "Problem(s) encountered migrating Objects API group "
                    f"'{group.name}'",
                    errors,
                )

            # if we ended up with multiple catalogues, internal consistency is broken!
            if len(catalogues_seen) > 1:
                self.has_errors = True
                catalogues_repr = ", ".join(
                    [f"{domain} ({rsin})" for domain, rsin in sorted(catalogues_seen)]
                )
                raise MigrationProblem(
                    "Problem(s) encountered migrating Objects API group "
                    f"'{group.name}'. Resolving the document types didn't converge to "
                    f"a single catalogue. Found: {catalogues_repr}.",
                )

            # it's possible none of the fields are configured and there's nothing to do
            if not fields_to_assign:
                continue

            # at this point, only a single catalogue has been resolved because there are
            # some field(s) to migrate, so do that.
            assert len(catalogues_seen) == 1, "Expected only a single catalogue."
            if catalogue is None:
                domain, rsin = catalogues_seen.pop()
                group.catalogue_domain = domain
                group.catalogue_rsin = rsin

            for field, value in fields_to_assign.items():
                setattr(group, field, value)

            group.save()

    def migrate_form_registration_backends(
        self, form: Form
    ) -> Mapping[str, Collection[str]]:
        summary: dict[str, Collection[str]] = {}
        for backend in form.registration_backends.all():
            backend_details: list[str] = []

            try:
                match backend.backend:
                    case "zgw-create-zaak":
                        has_changes = self.migrate_zgw_backend(backend)
                    case "objects_api":
                        has_changes = self.migrate_objects_api_backend(backend)
                    case _:  # pragma: no cover
                        continue
            except MigrationProblem as exc:
                self.has_errors = True
                backend_details.append(exc.message)
            except ExceptionGroup as exc_group:
                self.has_errors = True
                assert all(
                    isinstance(exc, MigrationProblem) for exc in exc_group.exceptions
                )
                messages = [exc_group.message] + [
                    f"- {getattr(exc, 'message', '(unknown)')}"
                    for exc in exc_group.exceptions
                ]
                backend_details += messages
            else:
                message = "Options update ok." if has_changes else "-"
                backend_details.append(message)

            summary[backend.name] = backend_details

        return summary

    def migrate_zgw_backend(self, backend: FormRegistrationBackend) -> bool:
        # XXX: object types integration is out of scope for 4.0, we can do something for
        # 4.1 though
        serializer = ZaakOptionsSerializer(
            data=backend.options,
            # we're not validating existing (modern) configuration, but migrating legacy
            # configuration. we'll ignore whatever is already configured in the new way
            context={"validate_business_logic": False},
        )
        is_valid = serializer.is_valid(raise_exception=False)
        if not is_valid:
            self.has_errors = True
            raise MigrationProblem("The registration options are not valid.")

        options: ZGWRegistrationOptions = serializer.validated_data

        api_group = options["zgw_api_group"]
        legacy_zaaktype_url = options["zaaktype"]
        legacy_documenttype_url = options["informatieobjecttype"]
        case_type_identification = options["case_type_identification"]
        document_type_description = options["document_type_description"]

        # new configuration is fully specified, legacy config is irrelevant
        if case_type_identification and document_type_description:
            return False

        # at this point at least legacy zaaktype or informatieobjecttype is still
        # used, because one the old/new fields is required for each type.
        catalogue: tuple[str, str] | None = None
        if "catalogue" in options:
            catalogue = options["catalogue"]["domain"], options["catalogue"]["rsin"]
        elif (domain := api_group.catalogue_domain) and (
            rsin := api_group.catalogue_rsin
        ):
            catalogue = (domain, rsin)

        # all references must resolve to objects within the same catalogue - if one
        # is already configured, all document types must resolve to the same one
        catalogues_seen: set[tuple[str, str]] = set()
        if catalogue is not None:
            catalogues_seen.add(catalogue)

        errors: list[MigrationProblem] = []

        # migrate the zaaktype and document type fields. Note that we also validate that
        # the document type is contained within the case type.
        if not case_type_identification:
            try:
                case_type_catalogue, case_typecase_type_identification = (
                    look_up_case_type(legacy_zaaktype_url)
                )
            except MigrationProblem as exc:
                errors.append(exc)
            else:
                catalogues_seen.add(case_type_catalogue)
                options["case_type_identification"] = case_typecase_type_identification

        if not document_type_description:
            try:
                doc_type_catalogue, document_type_description = look_up_document_type(
                    legacy_documenttype_url
                )
            except MigrationProblem as exc:
                errors.append(exc)
            else:
                # TODO: check that the document type is contained in the case type
                breakpoint()
                catalogues_seen.add(doc_type_catalogue)
                options["document_type_description"] = document_type_description

        # if we ran into resolution errors, now's the time to raise them
        if errors:
            self.has_errors = True
            raise ExceptionGroup("Problem(s) encountered:", errors)

        # if we ended up with multiple catalogues, internal consistency is broken!
        if len(catalogues_seen) > 1:
            self.has_errors = True
            catalogues_repr = ", ".join(
                [f"{domain} ({rsin})" for domain, rsin in sorted(catalogues_seen)]
            )
            raise MigrationProblem(
                "Resolving the case/document types didn't converge to a single "
                f"catalogue. Found: {catalogues_repr}.",
            )

        # at this point, only a single catalogue has been resolved because there are
        # some field(s) to migrate, so do that.
        assert len(catalogues_seen) == 1, "Expected only a single catalogue."
        if catalogue is None:
            domain, rsin = catalogues_seen.pop()
            _catalogue: CatalogueOption = {"domain": domain, "rsin": rsin}
            options["catalogue"] = _catalogue

        # serialize options backend save
        output_serializer = ZaakOptionsSerializer(instance=options)
        backend.options = output_serializer.data
        backend.save()

        return True

    def migrate_objects_api_backend(self, backend: FormRegistrationBackend) -> bool:
        OLD_TO_NEW_FIELD_MAPPING: Mapping[str, str] = {
            "informatieobjecttype_submission_report": "iot_submission_report",
            "informatieobjecttype_submission_csv": "iot_submission_csv",
            "informatieobjecttype_attachment": "iot_attachment",
        }

        serializer = ObjectsAPIOptionsSerializer(
            data=backend.options,
            # we're not validating existing (modern) configuration, but migrating legacy
            # configuration. we'll ignore whatever is already configured in the new way
            context={"validate_business_logic": False},
        )
        is_valid = serializer.is_valid(raise_exception=False)
        if not is_valid:
            self.has_errors = True
            raise MigrationProblem("The registration options are not valid.")

        options: ObjectsAPIRegistrationOptions = serializer.validated_data

        api_group = options["objects_api_group"]

        catalogue: tuple[str, str] | None = None
        if "catalogue" in options:
            catalogue = options["catalogue"]["domain"], options["catalogue"]["rsin"]
        elif (domain := api_group.catalogue_domain) and (
            rsin := api_group.catalogue_rsin
        ):
            catalogue = (domain, rsin)

        errors: list[MigrationProblem] = []
        fields_to_assign: dict[str, str] = {}

        # all references must resolve to objects within the same catalogue - if one
        # is already configured, all document types must resolve to the same one
        catalogues_seen: set[tuple[str, str]] = set()
        if catalogue is not None:
            catalogues_seen.add(catalogue)

        # check if there are fields that need to be migrated still, and validate
        # internal consistency
        for old_field, new_field in OLD_TO_NEW_FIELD_MAPPING.items():
            # if the reference is already configured, no need to bother with
            # migrating
            if options.get(new_field, ""):
                continue

            if not (legacy_url := options.get(old_field, "")):
                continue

            try:
                ((domain, rsin), description) = look_up_document_type(legacy_url)
            except MigrationProblem as exc:
                errors.append(exc)
                continue

            catalogues_seen.add((domain, rsin))
            fields_to_assign[new_field] = description

        # if we ran into resolution errors, now's the time to raise them
        if errors:
            self.has_errors = True
            raise ExceptionGroup("Problem(s) encountered:", errors)

        # if we ended up with multiple catalogues, internal consistency is broken!
        if len(catalogues_seen) > 1:
            self.has_errors = True
            catalogues_repr = ", ".join(
                [f"{domain} ({rsin})" for domain, rsin in sorted(catalogues_seen)]
            )
            raise MigrationProblem(
                "Resolving the document types didn't converge to a single catalogue. "
                f"Found: {catalogues_repr}.",
            )

        # it's possible none of the fields are configured and there's nothing to do
        if not fields_to_assign:
            return False

        # at this point, only a single catalogue has been resolved because there are
        # some field(s) to migrate, so do that.
        assert len(catalogues_seen) == 1, "Expected only a single catalogue."
        if catalogue is None:
            domain, rsin = catalogues_seen.pop()
            _catalogue: CatalogueOption = {"domain": domain, "rsin": rsin}
            options["catalogue"] = _catalogue

        for field, value in fields_to_assign.items():
            options[field] = value

        # serialize options backend save
        output_serializer = ObjectsAPIOptionsSerializer(instance=options)
        backend.options = output_serializer.data
        backend.save()

        return True
