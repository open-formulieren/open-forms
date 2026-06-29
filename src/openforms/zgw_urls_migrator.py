"""
Provide tooling to migrate component and registration configurations.

Legacy configuration used document/case type URLs towards the Documenten API, Zaken API
and Objects API. New configuration patterns allow specifying pointers that can resolve
the URLs at runtime. The migration from legacy to new pattern needs to be done before
4.0 is deployed, which drops support for the legacy configuration.
"""

from collections.abc import Collection, Iterator
from dataclasses import dataclass
from io import TextIOBase
from itertools import groupby

from django.db.models import Prefetch

from tabulate import tabulate

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.formio.typing import FileComponent
from openforms.forms.models import Form, FormDefinition, FormRegistrationBackend


@dataclass
class ComponentProblem:
    form: str
    step: str
    component: str


@dataclass
class APIGroupProblem:
    group: str
    type: str


@dataclass
class RegistrationBackendProblem:
    form: str
    backend: str
    backend_type: str


class Migrator:
    def __init__(self, outfile: TextIOBase):
        self.outfile = outfile

    def check(self) -> bool:
        """
        Run in check mode, making no changes but only reporting detected problems.

        :returns: ``False`` if problems are detected.
        """
        formio_config_migrator = FormioConfigurationMigrator(outfile=self.outfile)
        registration_backend_migrator = RegistrationBackendMigrator(
            outfile=self.outfile
        )
        component_problems = formio_config_migrator.check()
        registration_backend_problems, api_group_problems = (
            registration_backend_migrator.check()
        )

        # display detected problems
        if component_problems:
            self.outfile.write("🚨 Component problems detected.")
            self.outfile.write("")
            self.outfile.write(
                "   The Legacy `registration.informatieobjecttype` is not yet "
                "migrated to `registration.documentType`."
            )
            self.outfile.write("")
            component_problems = sorted(
                component_problems, key=lambda p: (p.form, p.step)
            )

            def report_component_problems() -> Iterator[tuple[str, str, str]]:
                for form, steps in groupby(component_problems, key=lambda p: p.form):
                    _form_repr = form
                    for step, problems in groupby(steps, key=lambda s: s.step):
                        _step_repr = step
                        for problem in problems:
                            yield (
                                _form_repr,
                                _step_repr,
                                problem.component,
                            )
                            _step_repr = ""
                            _form_repr = ""

            self.outfile.write(
                tabulate(
                    report_component_problems(),
                    headers=("Form", "Step", "Component"),
                    maxcolwidths=[50, 50, 100],
                )
            )
            self.outfile.write("")

        if api_group_problems:
            self.outfile.write("🚨 API group problems detected.")
            self.outfile.write("")
            self.outfile.write(
                "   The listed API groups still (partially) use legacy URLs."
            )
            self.outfile.write("")
            self.outfile.write(
                tabulate(
                    ((problem.group, problem.type) for problem in api_group_problems),
                    headers=("Group", "Type"),
                    maxcolwidths=[75, 50],
                )
            )

        if registration_backend_problems:
            self.outfile.write("🚨 Registration backend problems detected.")
            self.outfile.write("")
            self.outfile.write(
                "   The listed backends still (partially) use legacy URLs."
            )
            self.outfile.write("")
            registration_backend_problems = sorted(
                registration_backend_problems, key=lambda p: (p.form, p.backend)
            )

            def report_backend_problems() -> Iterator[tuple[str, str, str]]:
                for form, problems in groupby(
                    registration_backend_problems, key=lambda p: p.form
                ):
                    _form_repr = form
                    for problem in problems:
                        yield (_form_repr, problem.backend, problem.backend_type)
                        _form_repr = ""

            self.outfile.write(
                tabulate(
                    report_backend_problems(),
                    headers=("Form", "Backend", "Type"),
                    maxcolwidths=[75, 75, 50],
                )
            )
            self.outfile.write("")

        has_problems = (
            len(component_problems)
            + len(registration_backend_problems)
            + len(api_group_problems)
        ) > 0
        return not has_problems


def _get_form_repr(form: Form) -> str:
    return f"{form.admin_name} (ID:  {form.pk})"


class FormioConfigurationMigrator:
    has_errors: bool = False

    def __init__(self, outfile: TextIOBase):
        self.outfile = outfile
        self.forms_queryset = Form.objects.all()

    def _iter_form_defs(self, form: Form) -> Iterator[tuple[FormDefinition, str]]:
        for form_definition in FormDefinition.objects.filter(formstep__form=form):
            step_repr = f"{form_definition.admin_name} (ID: {form_definition.pk})"
            yield form_definition, step_repr

    @staticmethod
    def _iter_form_def_file_components(
        form_definition: FormDefinition,
    ) -> Iterator[FileComponent]:
        config_wrapper = form_definition.configuration_wrapper
        # loop over all components in the form definition and yield only the file
        # components
        for component in config_wrapper:
            match component["type"]:
                case "file":
                    yield component  # pyright: ignore[reportReturnType]
                case "editgrid":
                    # no special treatment needed, the child components are included in
                    # the config_wrapper already.
                    continue
                case _:
                    continue

    @staticmethod
    def check_file_component(component: FileComponent) -> bool:
        """
        Check whether the component needs a migration or not.
        """
        # no registration configuration at all - nothing to do
        if not (registration := component.get("registration")):
            return False

        # no legacy URL configured, do nothing
        if not registration.get("informatieobjecttype"):
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
        return True

    def check(self) -> Collection[ComponentProblem]:
        """
        Scan the (used) form definitions for file components with unmigrated URLs.
        """
        qs = self.forms_queryset
        problems: list[ComponentProblem] = []

        for form in qs.iterator():
            form_repr = _get_form_repr(form)
            for form_definition, step_repr in self._iter_form_defs(form):
                for component in self._iter_form_def_file_components(form_definition):
                    key = component["key"]
                    component_label = component.get("label", "")
                    component_repr = (
                        f"{component_label} ({key})" if component_label else key
                    )
                    needs_update = self.check_file_component(component)
                    if not needs_update:
                        continue
                    problems.append(
                        ComponentProblem(
                            form=form_repr,
                            step=step_repr,
                            component=component_repr,
                        )
                    )

        return problems


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
        self.forms_queryset = (
            Form.objects.filter(
                registration_backends__backend__in=REGISTRATION_PLUGIN_IDS
            )
            .prefetch_related(
                Prefetch(
                    "registration_backends",
                    queryset=FormRegistrationBackend.objects.filter(
                        backend__in=REGISTRATION_PLUGIN_IDS
                    ),
                )
            )
            .distinct()
        )
        self.objects_api_groups_queryset = ObjectsAPIGroupConfig.objects.exclude(
            informatieobjecttype_submission_report="",
            informatieobjecttype_submission_csv="",
            informatieobjecttype_attachment="",
        )

    @staticmethod
    def check_backend_needs_migration(backend: FormRegistrationBackend) -> bool:
        options = backend.options
        # we ignore invalid serializer data for the options - 4.0 can't be
        # blamed for broken upgrades if the configuration is already broken to begin
        # with
        match backend.backend:
            case "zgw-create-zaak":
                legacy_zaaktype_url = options.get("zaaktype")
                legacy_documenttype_url = options.get("informatieobjecttype")
                case_type_identification = options.get("case_type_identification")
                document_type_description = options.get("document_type_description")
                if legacy_zaaktype_url and not case_type_identification:
                    return True
                if legacy_documenttype_url and not document_type_description:
                    return True
                return False
            case "objects_api":
                catalogue = options.get("catalogue")
                informatieobjecttype_submission_report = options.get(
                    "informatieobjecttype_submission_report"
                )
                informatieobjecttype_submission_csv = options.get(
                    "informatieobjecttype_submission_csv"
                )
                informatieobjecttype_attachment = options.get(
                    "informatieobjecttype_attachment"
                )
                iot_submission_report = options.get("iot_submission_report")
                iot_submission_csv = options.get("iot_submission_csv")
                iot_attachment = options.get("iot_attachment")

                # as soon as a catalogue is specified in the options, it enables the
                # new document types, ignoring any legacy URLs configured
                if catalogue and catalogue != {"domain": "", "rsin": ""}:
                    return False

                # otherwise, all fields are optional, so only complain if there are
                # legacy URLs present
                if informatieobjecttype_submission_report and not iot_submission_report:
                    return True
                if informatieobjecttype_submission_csv and not iot_submission_csv:
                    return True
                if informatieobjecttype_attachment and not iot_attachment:
                    return True

                return False
            case _:  # pragma: no cover
                return False

    def check_api_groups(self) -> Collection[APIGroupProblem]:
        # we don't need to check ZGW API groups at all as there are no URLs configured
        # in there
        problems: list[APIGroupProblem] = []

        for group in self.objects_api_groups_queryset:
            submission_report_ok = (
                group.iot_submission_report
                or not group.informatieobjecttype_submission_report
            )
            submission_csv_ok = (
                group.iot_submission_csv
                or not group.informatieobjecttype_submission_csv
            )
            attachment_ok = (
                group.iot_attachment or not group.informatieobjecttype_attachment
            )
            if submission_report_ok and submission_csv_ok and attachment_ok:
                continue
            problems.append(APIGroupProblem(group=group.name, type="Objects API"))

        return problems

    def check(
        self,
    ) -> tuple[Collection[RegistrationBackendProblem], Collection[APIGroupProblem]]:
        api_group_problems = self.check_api_groups()
        backend_problems: list[RegistrationBackendProblem] = []
        for form in self.forms_queryset:
            form_repr = _get_form_repr(form)
            for backend in form.registration_backends.all():
                needs_migration = self.check_backend_needs_migration(backend)
                if not needs_migration:
                    continue
                backend_problems.append(
                    RegistrationBackendProblem(
                        form=form_repr,
                        backend=backend.name,
                        backend_type=backend.backend,
                    )
                )

        return (backend_problems, api_group_problems)
