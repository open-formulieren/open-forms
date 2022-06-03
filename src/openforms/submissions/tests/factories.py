import copy
from datetime import timedelta
from typing import List

from django.utils import timezone

import factory
from glom import PathAccessError, glom

from openforms.forms.models import FormVariable
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)

from ..constants import RegistrationStatuses, SubmissionValueVariableSources
from ..models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
    SubmissionStep,
    SubmissionValueVariable,
    TemporaryFileUpload,
)


class SubmissionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = Submission

    class Params:
        completed = factory.Trait(
            completed_on=factory.Faker("date_time_this_month", tzinfo=timezone.utc),
            created_on=factory.LazyAttribute(
                lambda s: s.completed_on - timedelta(hours=4)
            ),
            price=factory.PostGenerationMethodCall("calculate_price"),
        )
        registration_failed = factory.Trait(
            completed=True,
            last_register_date=factory.LazyFunction(timezone.now),
            registration_status=RegistrationStatuses.failed,
        )
        registration_success = factory.Trait(
            completed=True,
            last_register_date=factory.LazyFunction(timezone.now),
            registration_status=RegistrationStatuses.success,
        )
        registration_pending = factory.Trait(
            completed=True,
            last_register_date=None,
            registration_status=RegistrationStatuses.pending,
        )
        registration_in_progress = factory.Trait(
            completed=True,
            last_register_date=factory.LazyFunction(timezone.now),
            registration_status=RegistrationStatuses.in_progress,
        )
        has_previous_submission = factory.Trait(
            previous_submission=factory.SubFactory(
                "openforms.submissions.tests.factories.SubmissionFactory",
                form=factory.SelfAttribute("..form"),
            )
        )
        with_report = factory.Trait(
            report=factory.RelatedFactory(
                "openforms.submissions.tests.factories.SubmissionReportFactory",
                factory_related_name="submission",
            )
        )
        with_hashed_identifying_attributes = factory.Trait(
            _hashed_id_attrs=factory.PostGenerationMethodCall(
                "hash_identifying_attributes"
            ),
        )

    @classmethod
    def from_components(
        cls,
        components_list: List[dict],
        submitted_data: dict = None,
        **kwargs,
    ) -> Submission:
        """
        generate a complete
        Form/FormStep/FormDefinition/FormVariable + Submission/SubmissionStep/SubmissionValueVariable
        tree from a list of formio components

        remember to generate from privates.test import temp_private_root
        """
        kwargs.setdefault("with_report", True)
        submission = cls.create(**kwargs)
        form = submission.form

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

        data = submitted_data or {}
        SubmissionStepFactory.create(
            submission=submission, form_step=form_step, data=data
        )

        # When the submission was initially created, the method calculate_price has already
        # loaded the submission_value_variables_state, but no submission variables existed at that point.
        submission.load_submission_value_variables_state(refresh=True)
        return submission

    @staticmethod
    def from_data(data_dict: dict, **kwargs):
        components = [
            {
                "key": key,
            }
            for key in data_dict
        ]
        return SubmissionFactory.from_components(
            components,
            data_dict,
            **kwargs,
        )


class SubmissionStepFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)
    form_step = factory.SubFactory(
        FormStepFactory, form=factory.SelfAttribute("..submission.form")
    )

    class Meta:
        model = SubmissionStep

    @classmethod
    def create(
        cls,
        **kwargs,
    ) -> SubmissionStep:

        step_data = kwargs.pop("data", {})
        submission_step = super().create(**kwargs)

        form_variables = submission_step.submission.form.formvariable_set.all()

        for variable in form_variables:
            try:
                value = glom(step_data, variable.key)
            except PathAccessError:
                continue

            SubmissionValueVariableFactory.create(
                submission=submission_step.submission,
                key=variable.key,
                value=value,
                form_variable=variable,
            )

        return submission_step


class SubmissionReportFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("bs")
    content = factory.django.FileField(filename="submission_report.pdf")
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = SubmissionReport


class TemporaryFileUploadFactory(factory.django.DjangoModelFactory):
    file_name = factory.Faker("file_name")
    content_type = factory.Faker("mime_type")
    content = factory.django.FileField(filename="file.dat", data=b"content")

    class Meta:
        model = TemporaryFileUpload


class SubmissionFileAttachmentFactory(factory.django.DjangoModelFactory):
    submission_step = factory.SubFactory(SubmissionStepFactory)
    temporary_file = factory.SubFactory(TemporaryFileUploadFactory)
    content = factory.django.FileField(filename="attachment.pdf", data=b"content")
    form_key = factory.Faker("bs")
    file_name = factory.Faker("file_name")
    original_name = factory.Faker("file_name")
    content_type = factory.Faker("mime_type")

    class Meta:
        model = SubmissionFileAttachment

    @classmethod
    def create(
        cls,
        **kwargs,
    ) -> SubmissionFileAttachment:
        file_attachment = super().create(**kwargs)

        submission = file_attachment.submission_step.submission
        form_variable = submission.form.formvariable_set.filter(
            key=file_attachment.form_key
        ).first()

        if not form_variable:
            form_variable = FormVariableFactory.create(
                form=submission.form,
                form_definition=file_attachment.submission_step.form_step.form_definition,
                key=file_attachment.form_key,
            )

        submission_variable = submission.submissionvaluevariable_set.filter(
            key=file_attachment.form_key
        ).first()
        if not submission_variable:
            submission_variable = SubmissionValueVariableFactory.create(
                submission=submission,
                key=file_attachment.form_key,
                form_variable=form_variable,
            )

        file_attachment.submission_variable = submission_variable
        file_attachment.save()

        return file_attachment


class SubmissionValueVariableFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)
    form_variable = factory.SubFactory(FormVariableFactory)
    key = factory.SelfAttribute("form_variable.key")
    source = SubmissionValueVariableSources.user_input

    class Meta:
        model = SubmissionValueVariable
