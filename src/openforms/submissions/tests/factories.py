import copy
from typing import List

import factory

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..models import Submission, SubmissionReport, SubmissionStep


class SubmissionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = Submission

    @staticmethod
    def from_components(
        components_list: List[dict],
        submitted_data: dict = None,
        form_kwargs: dict = None,
        submission_kwargs: dict = None,
    ) -> Submission:
        """
        generate a complete Form/FormStep/FormDefinition + Submission/SubmissionStep tree from a list of formio components

        optionally: supply a dictionary with data (keys must match the component keys)
        optionally: supply kwargs for the Form and Submission factories (name, bsn etc)
        """
        if form_kwargs is None:
            form_kwargs = dict()
        if submission_kwargs is None:
            submission_kwargs = dict()

        form = FormFactory.create(**form_kwargs)
        submission = SubmissionFactory.create(form=form, **submission_kwargs)

        components = list()

        for _comp in components_list:
            component = copy.deepcopy(_comp)
            key = component["key"]
            # convenience
            if not component.get("label"):
                component["label"] = key.title()
            if not component.get("type"):
                component["type"] = "text"

            components.append(component)

        configuration = {"components": components}

        form_definition = FormDefinitionFactory.create(
            name=f"definition-{key}", configuration=configuration
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        SubmissionStepFactory.create(
            submission=submission, form_step=form_step, data=submitted_data
        )

        SubmissionReportFactory.create(submission=submission)

        return submission

    @staticmethod
    def from_data(data_dict, form_kwargs: dict = None, submission_kwargs: dict = None):
        components = [
            {
                "key": key,
            }
            for key in data_dict
        ]
        return SubmissionFactory.from_components(
            components,
            data_dict,
            form_kwargs=form_kwargs,
            submission_kwargs=submission_kwargs,
        )


class SubmissionStepFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = SubmissionStep


class SubmissionReportFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("bs")
    content = factory.django.FileField(filename="submission_report.pdf")
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = SubmissionReport
