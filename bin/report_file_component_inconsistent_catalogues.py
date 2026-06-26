#!/usr/bin/env python
#
# Introspect file components used in forms with the ZGW or Objects API registration
# plugin and report which file components resolved to a different catalogue than the
# one in the registration plugin settings.
#
# This check is intended to run *after* the data migrations that copied all the
# configuration to the individual registration backends. It cannot be run in a
# preventive manner as upgrade check because these problems cannot be corrected pre-4.0.
#
from __future__ import annotations

import sys
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

import django
from django.db.models import Prefetch

import click
from tabulate import tabulate

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))

if TYPE_CHECKING:
    from openforms.formio.typing import FileComponent


def iter_file_components(form) -> Iterator[FileComponent]:
    from openforms.formio.service import iter_components

    step_components_generator = (
        iter_components(
            step.form_definition.configuration,
            recursive=True,
            recurse_into_editgrid=True,
        )
        for step in form.formstep_set.all()
    )
    for component in chain.from_iterable(step_components_generator):
        if component["type"] != "file":
            continue
        yield component  # pyright: ignore[reportReturnType]


@dataclass
class Problem:
    form_name: str
    form_id: int
    registration_backend_name: str
    registration_backend_type: str
    component_key: str


def report_components() -> bool:
    """
    Scan forms with file components and ZGW APIs/Objects API registration plugin usage.

    :returns: ``True`` if no problems are detected, ``False`` if there are issues
      detected.
    """
    from openforms.forms.models import Form, FormRegistrationBackend, FormStep
    from openforms.registrations.contrib.objects_api.constants import (
        PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
    )
    from openforms.registrations.contrib.zgw_apis.plugin import (
        PLUGIN_IDENTIFIER as ZGW_APIS_PLUGIN_IDENTIFIER,
    )
    from openforms.registrations.contrib.zgw_apis.typing import CatalogueOption

    RELEVANT_BACKENDS = {
        OBJECTS_API_PLUGIN_IDENTIFIER,
        ZGW_APIS_PLUGIN_IDENTIFIER,
    }

    forms = (
        Form.objects.prefetch_related(
            Prefetch(
                "registration_backends",
                queryset=FormRegistrationBackend.objects.filter(
                    backend__in=RELEVANT_BACKENDS
                ),
            ),
            Prefetch(
                "formstep_set",
                queryset=FormStep.objects.select_related("form_definition"),
            ),
        )
        .filter(registration_backends__backend__in=RELEVANT_BACKENDS)
        .distinct()
    )
    problems: list[Problem] = []
    for form in forms.iterator(chunk_size=10):
        file_component_catalogues: dict[str, CatalogueOption] = {}

        for file_component in iter_file_components(form):
            # check the catalogue that's specified or resolved by the migration tool on
            # 3.5. The data migration copies the configuration, but leaves the old
            # configuration on the component, so we can easily test this catalogue
            # against the registration backend catalogues without doing network IO.
            if not (registration := file_component.get("registration")):
                continue
            if not (document_type := registration.get("documentType")):
                continue
            if not (catalogue := document_type.get("catalogue")):
                continue
            file_component_catalogues[file_component["key"]] = catalogue

        # nothing to check, bail early
        if not file_component_catalogues:
            continue

        for backend in form.registration_backends.all():
            # compare the catalogue of the backend with the files
            backend_catalogue = backend.options.get("catalogue", {})
            for key, catalogue in file_component_catalogues.items():
                if catalogue == backend_catalogue:
                    continue
                problems.append(
                    Problem(
                        form_name=form.admin_name,
                        form_id=form.pk,
                        registration_backend_name=backend.name,
                        registration_backend_type=backend.backend,
                        component_key=key,
                    )
                )

    if not problems:
        click.echo(click.style("No inconsistencies found.", fg="green"))
        return True

    def _report_problems() -> Iterator[tuple[str, str, str, str, str]]:
        form_id: int = 0
        backend_name = ""

        for problem in problems:
            form_id_changed = problem.form_id != form_id
            form_id = problem.form_id

            backend_name_changed = problem.registration_backend_name != backend_name
            backend_name = problem.registration_backend_name

            yield (
                problem.form_name if form_id_changed else "",
                str(form_id) if form_id_changed else "",
                backend_name if backend_name_changed else "",
                problem.registration_backend_type if backend_name_changed else "",
                problem.component_key,
            )

    click.echo(
        click.style(
            "Found file components with a different catalogue than the registration "
            "backend.",
            fg="red",
        )
    )
    click.echo("")
    click.echo(
        tabulate(
            _report_problems(),
            headers=(
                "Form admin name",
                "Form ID",
                "Registration backend name",
                "Registration backend type",
                "File upload component key",
            ),
        )
    )

    return False


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return report_components()


if __name__ == "__main__":
    main()
