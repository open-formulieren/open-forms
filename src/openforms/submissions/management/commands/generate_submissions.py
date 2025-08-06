from uuid import uuid4

from django.core.management import BaseCommand

from tqdm import tqdm

from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.submissions.models.submission import Submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument("--amount", type=int, default=100)

    def handle(self, **options):
        # one form - 4 steps, 5 components per step -> 20 component form variables per form
        form = FormFactory.create(category=None, slug=str(uuid4()))
        steps = FormStepFactory.create_batch(
            4,
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "field1",
                        "label": "field 1",
                    },
                    {
                        "type": "textfield",
                        "key": "field2",
                        "label": "field 2",
                    },
                    {
                        "type": "textfield",
                        "key": "field3",
                        "label": "field 3",
                    },
                    {
                        "type": "textfield",
                        "key": "field4",
                        "label": "field 4",
                    },
                    {
                        "type": "textfield",
                        "key": "field5",
                        "label": "field 5",
                    },
                ]
            },
        )
        # + 5 user defined variables
        ud_variables = FormVariableFactory.create_batch(5, form=form, user_defined=True)
        self.stdout.write("Created form definition.")

        # now create submissions
        amount = options["amount"]
        for submission in tqdm(
            SubmissionFactory.create_batch(amount, form=form), dynamic_ncols=True
        ):
            for step in steps:
                SubmissionStepFactory.create(
                    submission=submission,
                    form_step=step,
                    data={
                        "field1": "value 1",
                        "field2": "value 2",
                        "field3": "value 3",
                        "field4": "value 4",
                        "field5": "value 5",
                    },
                )
            for form_variable in ud_variables:
                SubmissionValueVariableFactory.create(
                    submission=submission, key=form_variable.key
                )

        self.stdout.write(f"There are now {Submission.objects.count()} submissions.")
