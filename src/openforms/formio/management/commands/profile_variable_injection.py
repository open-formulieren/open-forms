import json
import timeit
from contextlib import contextmanager
from copy import deepcopy
from functools import partial
from pathlib import Path

from django.core.management import BaseCommand
from django.db import connection
from django.template import Context, Template, TemplateSyntaxError

from glom import GlomError, assign, glom

from openforms.forms.models import Form
from openforms.forms.tests.factories import (
    FormFactory,
    FormVariableDataTypes,
    FormVariableFactory,
    FormVariableSources,
)
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ...utils import iter_components

CURRENT_DIR = Path(__file__).parent.resolve()

TEMPLATE_PROPERTIES = [
    "label",
    "legend",
    "defaultValue",
    "description",
    "html",
]


with open(CURRENT_DIR / "profiling_formio.json", "r") as infile:
    CONFIGURATION = json.load(infile)


@contextmanager
def count_queries(stdout):
    num_before = len(connection.queries)
    yield
    num_after = len(connection.queries)
    stdout.write(f"Did {num_after - num_before} database queries.")


def interpolate_config(configuration, variables):
    context = Context({key: variable.value for key, variable in variables.items()})
    for component in iter_components(configuration):
        inject_variables(component, context)
    return configuration


def inject_variables(component: dict, context):
    for spec in TEMPLATE_PROPERTIES:
        try:
            possible_template = glom(component, spec)
        except GlomError:
            continue

        try:
            template = Template(possible_template)
        except TemplateSyntaxError:
            continue

        result = template.render(context)
        assign(component, spec, result)


def get_num_components(configuration) -> int:
    return len(list(iter_components(configuration)))


class Command(BaseCommand):
    help = "Run profiler for template-based variable injection in formio configuration."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--outfile", help="Write result to filepath")
        parser.add_argument(
            "--number", help="timeit module iterations number", type=int, default=100
        )
        parser.add_argument(
            "--config-scale",
            default="1,10,100",
            help="Comma-separated list of integers to scale the number of formio config components with.",
        )

    def handle(self, **options):
        form = self._setup_form()
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form.formstep_set.get(),
            data={
                "naam": "Maykin",
                "tussenvoegsel": "",
                "achternaam": "Media",
                "postcode": "1015 CJ",
            },
        )
        state = submission.load_submission_value_variables_state()
        variables = state.variables

        self.basic_call = partial(interpolate_config, variables=variables)

        # logging the result / checking the interpolation itself.
        if options["outfile"]:
            self.stdout.write(
                "Interpolating variables in configuration and saving the result."
            )
            with count_queries(stdout=self.stdout):
                config = self.basic_call(configuration=deepcopy(CONFIGURATION))

            with open(options["outfile"], "w") as outfile:
                json.dump(config, outfile, indent=2)

        self.number = options["number"]

        # actual profiling
        scale_factors = [int(x) for x in options["config_scale"].split(",")]
        for factor in scale_factors:
            configuration = {
                **CONFIGURATION,
                "components": deepcopy(CONFIGURATION["components"]) * factor,
            }
            self.stdout.write(f"Configuration components scale factor: {factor}")
            self._profile(configuration, variables)
            self.stdout.write("")

    def _profile(self, configuration, variables):
        number = self.number
        self.stdout.write(
            f"Input configuration has {get_num_components(configuration)} components."
        )
        duration = timeit.timeit(
            partial(self.basic_call, configuration=configuration), number=number
        )
        duration_per_loop = duration / number
        duration_usec = duration_per_loop / 1e-3
        self.stdout.write(f"{number} loop(s), average duration: {duration_usec:.3f}ms")

    @staticmethod
    def _setup_form():
        slug = "formio-interpolation-profiling"
        form = Form.objects.filter(slug=slug).first()
        if form is None:
            form = FormFactory.create(
                generate_minimal_setup=True,
                formstep__form_definition__configuration=CONFIGURATION,
                formstep__form_definition__slug=slug,
            )
            # create user-defined variables
            FormVariableFactory.create(
                form=form,
                key="fieldsetLabel",
                form_definition=None,
                source=FormVariableSources.user_defined,
                data_type=FormVariableDataTypes.string,
                initial_value="A group",
            )
            FormVariableFactory.create(
                form=form,
                key="labels",
                form_definition=None,
                source=FormVariableSources.user_defined,
                data_type=FormVariableDataTypes.object,
                initial_value={
                    "firstName": "Voornaam",
                    "lastName": "Achternaam",
                },
            )
            FormVariableFactory.create(
                form=form,
                key="defaultPostcode",
                form_definition=None,
                source=FormVariableSources.user_defined,
                data_type=FormVariableDataTypes.string,
                initial_value="1015 CJ",
            )
        return form
