"""
Provide tooling to migrate component and registration configurations.

Legacy configuration used document/case type URLs towards the Documenten API, Zaken API
and Objects API. New configuration patterns allow specifying pointers that can resolve
the URLs at runtime. The migration from legacy to new pattern needs to be done before
4.0 is deployed, which drops support for the legacy configuration.
"""

from collections.abc import Iterator, Mapping
from io import TextIOBase

from tabulate import tabulate
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.zgw.clients.catalogi import Catalogus, InformatieObjectType
from openforms.formio.typing import FileComponent
from openforms.forms.models import Form, FormDefinition


class Migrator:
    def __init__(self, outfile: TextIOBase):
        self.outfile = outfile

    def migrate(self) -> None:
        formio_config_migrator = FormioConfigurationMigrator(outfile=self.outfile)

        formio_config_migrator.migrate()


class ComponentMigrationProblem(Exception):
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


class FormioConfigurationMigrator:
    processed_fds: set[int] = set()

    def __init__(self, outfile: TextIOBase):
        self.outfile = outfile

    def migrate(self) -> None:
        """
        Migrate all forms in the environment.
        """

        def _run() -> Iterator[tuple[str, str, str]]:
            for form in Form.objects.all().iterator():
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
                    except ComponentMigrationProblem as exc:
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
        if (
            registration.get("description")
            and (catalogue := registration.get("catalogue"))
            and catalogue.get("domain")
            and catalogue.get("string")
        ):
            return False

        # look up the document type and fill out the catalogue + description
        service = Service.get_service(url=legacy_url)
        if service is None:
            raise ComponentMigrationProblem(
                f"No service configured (url: {legacy_url})."
            )

        client = build_client(service=service)
        response = client.get(url=legacy_url)
        if not response.ok:
            raise ComponentMigrationProblem(
                f"Documenttype URL response: HTTP {response.status_code} "
                f"(url: {legacy_url})"
            )

        iot: InformatieObjectType = response.json()

        catalogus_url = iot["catalogus"]
        catalogus_response = client.get(url=catalogus_url)
        if not response.ok:
            raise ComponentMigrationProblem(
                f"Catalogus URL response: HTTP {catalogus_response.status_code} "
                f"(url: {catalogus_url})"
            )

        catalogus: Catalogus = catalogus_response.json()

        component["registration"]["documentType"] = {  # pyright: ignore[reportGeneralTypeIssues]
            "catalogue": {
                "domain": catalogus["domein"],
                "rsin": catalogus["rsin"],
            },
            "description": iot["omschrijving"],
        }

        return True


class RegistrationBackendMigrator:
    pass


class ZGWAPIsMigrator(RegistrationBackendMigrator):
    pass


class ObjectsAPIMigrator(RegistrationBackendMigrator):
    pass
