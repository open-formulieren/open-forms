import copy
from datetime import timedelta
from typing import List, Optional

from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language

import factory
import magic
from glom import PathAccessError, glom

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.payments.constants import PaymentStatus

from ..constants import (
    PostSubmissionEvents,
    RegistrationStatuses,
    SubmissionValueVariableSources,
)
from ..models import (
    PostCompletionMetadata,
    Submission,
    SubmissionFileAttachment,
    SubmissionReport,
    SubmissionStep,
    SubmissionValueVariable,
    TemporaryFileUpload,
)


class SubmissionFactory(factory.django.DjangoModelFactory):

    # this repeats the default of the Charfield LazyAttribute evaluation needs;
    # stub.factory_parent.__getattr__ cs. doesn't check the model's attributes.
    language_code = factory.LazyAttribute(lambda _: get_language())

    form = factory.SubFactory(
        FormFactory,
        translation_enabled=factory.LazyAttribute(
            lambda stub: stub.factory_parent.language_code != settings.LANGUAGE_CODE
        ),
    )

    class Meta:
        model = Submission

    class Params:
        completed = factory.Trait(
            completed_on=factory.Faker("date_time_this_month", tzinfo=timezone.utc),
            created_on=factory.LazyAttribute(
                lambda s: s.completed_on - timedelta(hours=4)
            ),
            pre_registration_completed=True,
            price=factory.PostGenerationMethodCall("calculate_price"),
            metadata=factory.RelatedFactory(
                "openforms.submissions.tests.factories.PostCompletionMetadataFactory",
                factory_related_name="submission",
                tasks_ids=["some-id"],
                trigger_event=PostSubmissionEvents.on_completion,
            ),
        )
        completed_not_preregistered = factory.Trait(
            completed_on=factory.Faker("date_time_this_month", tzinfo=timezone.utc),
            created_on=factory.LazyAttribute(
                lambda s: s.completed_on - timedelta(hours=4)
            ),
            price=factory.PostGenerationMethodCall("calculate_price"),
        )
        suspended = factory.Trait(
            suspended_on=factory.Faker("date_time_this_month", tzinfo=timezone.utc),
            completed_on=None,
            auth_info__with_hashed_identifying_attributes=True,
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
            pre_registration_completed=True,
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
            pre_registration_completed=True,
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
        with_completed_payment = factory.Trait(
            form__payment_backend="demo",
            product=factory.RelatedFactory(
                "openforms.payments.tests.factories.SubmissionPaymentFactory",
                factory_related_name="submission",
                status=PaymentStatus.completed,
            ),
        )
        with_registered_payment = factory.Trait(
            form__payment_backend="demo",
            product=factory.RelatedFactory(
                "openforms.payments.tests.factories.SubmissionPaymentFactory",
                factory_related_name="submission",
                status=PaymentStatus.registered,
            ),
        )

    @factory.post_generation
    def prefill_data(obj, create, extracted, **kwargs):
        state = obj.load_submission_value_variables_state()
        if extracted:
            state.save_prefill_data(extracted)
        return extracted

    @factory.post_generation
    def auth_info(obj, create, extracted, **kwargs):
        if (extracted is None and not kwargs) or not create:
            return

        from openforms.authentication.tests.factories import AuthInfoFactory

        kwargs["submission"] = obj
        AuthInfoFactory.create(**kwargs)

    @classmethod
    def from_components(
        cls,
        components_list: List[dict],
        submitted_data: dict | None = None,
        form_definition_kwargs: dict | None = None,
        **kwargs,
    ) -> Submission:
        """
        generate a complete
        Form/FormStep/FormDefinition/FormVariable + Submission/SubmissionStep/SubmissionValueVariable
        tree from a list of formio components

        remember to generate from privates.test import temp_private_root
        """
        kwargs.setdefault("with_report", True)

        bsn = kwargs.pop("bsn", None)
        kvk = kwargs.pop("kvk", None)
        pseudo = kwargs.pop("pseudo", None)
        auth_plugin = kwargs.pop("auth_plugin", None)

        submission = cls.create(**kwargs)
        if bsn or kvk or pseudo:
            from openforms.authentication.constants import AuthAttribute
            from openforms.authentication.tests.factories import AuthInfoFactory

            attribute = AuthAttribute.bsn
            if kvk:
                attribute = AuthAttribute.kvk
            elif pseudo:
                attribute = AuthAttribute.pseudo

            attrs = {
                "value": bsn or kvk or pseudo,
                "attribute": attribute,
                "submission": submission,
            }
            if auth_plugin:
                attrs["plugin"] = auth_plugin
            AuthInfoFactory.create(**attrs)

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

        form_definition_index = cls._setup_next_sequence()
        form_definition_kwargs = form_definition_kwargs or {}
        form_definition_kwargs.setdefault("name", f"definition-{form_definition_index}")
        form_definition_kwargs.setdefault("configuration", configuration)

        form_definition = FormDefinitionFactory.create(**form_definition_kwargs)
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        data = submitted_data or {}
        SubmissionStepFactory.create(
            submission=submission, form_step=form_step, data=data
        )

        # When the submission was initially created, the method calculate_price has already
        # loaded the submission_value_variables_state, but no submission variables existed at that point.
        submission.load_execution_state(refresh=True)
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

        if hasattr(submission_step.submission, "_variables_state"):
            del submission_step.submission._variables_state

        return submission_step


class SubmissionReportFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("bs")
    content = factory.django.FileField(filename="submission_report.pdf")
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = SubmissionReport


class TemporaryFileUploadFactory(factory.django.DjangoModelFactory):
    file_name = factory.Faker("file_name")
    content = factory.django.FileField(filename="file.dat", data=b"content")

    class Meta:
        model = TemporaryFileUpload

    @factory.lazy_attribute
    def content_type(self) -> str:
        buffer = self.content.read(2048)
        return magic.from_buffer(buffer, mime=True)


class SubmissionFileAttachmentFactory(factory.django.DjangoModelFactory):
    submission_step = factory.SubFactory(SubmissionStepFactory)
    temporary_file = factory.SubFactory(TemporaryFileUploadFactory)
    content = factory.django.FileField(filename="attachment.pdf", data=b"content")
    file_name = factory.Faker("file_name")
    original_name = factory.Faker("file_name")
    content_type = factory.Faker("mime_type")

    class Meta:
        model = SubmissionFileAttachment

    @classmethod
    def create(
        cls,
        form_key: Optional[str] = None,
        **kwargs,
    ) -> SubmissionFileAttachment:
        file_attachment = super().create(**kwargs)

        # this is no longer a field on the model, but we still want to use the form/sub-variable generating machinery below
        if form_key is None:
            form_key = factory.Faker("slug").generate()

        submission = file_attachment.submission_step.submission
        form_variable = submission.form.formvariable_set.filter(key=form_key).first()

        if not form_variable:
            form_variable = FormVariableFactory.create(
                form=submission.form,
                form_definition=file_attachment.submission_step.form_step.form_definition,
                key=form_key,
            )

        submission_variable = submission.submissionvaluevariable_set.filter(
            key=form_key
        ).first()
        if not submission_variable:
            submission_variable = SubmissionValueVariableFactory.create(
                submission=submission,
                key=form_key,
                form_variable=form_variable,
            )

        file_attachment.submission_variable = submission_variable
        file_attachment.save()

        return file_attachment


class SubmissionValueVariableFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)
    form_variable = factory.SubFactory(
        FormVariableFactory,
        form=factory.SelfAttribute("..submission.form"),
        key=factory.SelfAttribute("..key"),
    )
    key = factory.Faker("word")
    source = SubmissionValueVariableSources.user_input
    is_initially_prefilled = factory.LazyAttribute(
        lambda submission_value_var: (
            submission_value_var.form_variable.prefill_plugin != ""
            if submission_value_var.form_variable
            else False
        )
    )

    class Meta:
        model = SubmissionValueVariable
        django_get_or_create = ("submission", "form_variable")


class PostCompletionMetadataFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = PostCompletionMetadata
