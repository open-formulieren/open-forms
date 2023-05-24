import json
import zipfile
from pathlib import Path
from textwrap import dedent

from django.core.management import call_command
from django.test import TestCase, override_settings, tag
from django.utils import translation

from freezegun import freeze_time

from openforms.emails.models import ConfirmationEmailTemplate
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory
from openforms.products.tests.factories import ProductFactory
from openforms.translations.tests.utils import make_translated
from openforms.variables.constants import FormVariableSources
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ..constants import EXPORT_META_KEY
from ..models import Form, FormDefinition, FormLogic, FormStep, FormVariable
from ..utils import form_to_json
from .factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)

PATH = Path(__file__).parent


class ImportExportTests(TestCase):
    def setUp(self):
        self.filepath = PATH / "export_test.zip"
        self.addCleanup(lambda: self.filepath.unlink(missing_ok=True))

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_export(self):
        form, _ = FormFactory.create_batch(2, authentication_backends=["demo"])
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormStepFactory.create()
        FormLogicFactory.create(
            form=form,
            actions=[
                {
                    "component": "test_component",
                    "action": {
                        "type": "disable-next",
                    },
                }
            ],
        )
        FormVariableFactory.create(
            form=form, source=FormVariableSources.user_defined, key="test-user-defined"
        )

        call_command("export", form.pk, self.filepath)

        with zipfile.ZipFile(self.filepath, "r") as f:
            self.assertEqual(
                f.namelist(),
                [
                    "forms.json",
                    "formSteps.json",
                    "formDefinitions.json",
                    "formLogic.json",
                    "formVariables.json",
                    f"{EXPORT_META_KEY}.json",
                ],
            )

            forms = json.loads(f.read("forms.json"))
            self.assertEqual(len(forms), 1)
            self.assertEqual(forms[0]["uuid"], str(form.uuid))
            self.assertEqual(forms[0]["name"], form.name)
            self.assertEqual(forms[0]["internal_name"], form.internal_name)
            self.assertEqual(forms[0]["slug"], form.slug)
            self.assertEqual(forms[0]["authentication_backends"], ["demo"])
            self.assertEqual(len(forms[0]["steps"]), form.formstep_set.count())
            self.assertIsNone(forms[0]["product"])

            form_definitions = json.loads(f.read("formDefinitions.json"))
            self.assertEqual(len(form_definitions), 1)
            self.assertEqual(form_definitions[0]["uuid"], str(form_definition.uuid))
            self.assertEqual(form_definitions[0]["name"], form_definition.name)
            self.assertEqual(
                form_definitions[0]["internal_name"], form_definition.internal_name
            )
            self.assertEqual(form_definitions[0]["slug"], form_definition.slug)
            self.assertEqual(
                form_definitions[0]["configuration"],
                form_definition.configuration,
            )

            form_steps = json.loads(f.read("formSteps.json"))
            self.assertEqual(len(form_steps), 1)
            self.assertEqual(
                form_steps[0]["configuration"], form_definition.configuration
            )

            form_logic = json.loads(f.read("formLogic.json"))
            self.assertEqual(1, len(form_logic))
            self.assertEqual("test_component", form_logic[0]["actions"][0]["component"])
            self.assertEqual(
                {"type": "disable-next"}, form_logic[0]["actions"][0]["action"]
            )
            self.assertIn(str(form.uuid), form_logic[0]["form"])

            form_variables = json.loads(f.read("formVariables.json"))
            # Only user defined form variables are included in the export
            self.assertEqual(len(form_variables), 1)
            self.assertEqual(
                FormVariableSources.user_defined, form_variables[0]["source"]
            )

    def test_import(self):
        product = ProductFactory.create()
        merchant = OgoneMerchantFactory.create()
        form = FormFactory.create(
            product=product,
            authentication_backends=["digid"],
            registration_backend="email",
            registration_backend_options={
                "to_emails": ["foo@bar.baz"],
                "attach_files_to_email": None,
            },
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": merchant.id},
        )
        form_definition = FormDefinitionFactory.create(
            configuration={"components": [{"key": "test-key", "type": "textfield"}]}
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        FormVariableFactory.create(
            form=form, user_defined=True, key="test-user-defined"
        )

        # fetch configurations are not exported (yet)
        # but shouldn't break export - import
        fetch_config = ServiceFetchConfigurationFactory.create()
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!": {"var": "test-user-defined"}},
            actions=[
                {
                    "action": {"type": "fetch-from-service", "value": fetch_config.pk},
                    "variable": "test-user-defined",
                }
            ],
        )

        form_logic = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "test-user-defined"}, 1]},
            actions=[
                {
                    "action": {"type": "step-not-applicable"},
                    "form_step_uuid": str(form_step.uuid),
                }
            ],
        )

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        call_command("export", form.pk, self.filepath)

        # attempt to break ForeignKey constraint
        fetch_config.delete()

        old_form_definition_slug = form_definition.slug
        form_definition.slug = "modified"
        form_definition.save()

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        call_command("import", import_file=self.filepath)

        forms = Form.objects.all()
        imported_form = forms.last()
        self.assertEqual(forms.count(), 2)
        self.assertNotEqual(imported_form.pk, form_pk)
        self.assertNotEqual(imported_form.uuid, str(form.uuid))
        self.assertEqual(imported_form.active, False)
        self.assertEqual(imported_form.registration_backend, form.registration_backend)
        self.assertEqual(
            imported_form.registration_backend_options,
            form.registration_backend_options,
        )
        self.assertEqual(imported_form.name, form.name)
        self.assertIsNone(imported_form.product)
        self.assertEqual(imported_form.slug, old_form_slug)
        self.assertEqual(imported_form.authentication_backends, ["digid"])
        self.assertEqual(imported_form.payment_backend, "ogone-legacy")
        self.assertEqual(
            imported_form.payment_backend_options, {"merchant_id": merchant.id}
        )

        form_definitions = FormDefinition.objects.all()
        fd2 = form_definitions.last()
        self.assertEqual(form_definitions.count(), 2)
        self.assertNotEqual(fd2.pk, form_definition_pk)
        self.assertNotEqual(fd2.uuid, str(form_definition.uuid))
        self.assertEqual(fd2.configuration, form_definition.configuration)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.slug, old_form_definition_slug)

        form_steps = FormStep.objects.all()
        fs2 = form_steps.get(form=imported_form)
        self.assertEqual(form_steps.count(), 2)
        self.assertNotEqual(fs2.pk, form_step_pk)
        self.assertNotEqual(fs2.uuid, str(form_step.uuid))
        self.assertEqual(fs2.form.pk, imported_form.pk)
        self.assertEqual(fs2.form_definition.pk, fd2.pk)
        self.assertEqual(fs2.order, form_step.order)

        user_defined_vars = FormVariable.objects.filter(
            source=FormVariableSources.user_defined
        )
        self.assertEqual(2, user_defined_vars.count())

        form_logics = FormLogic.objects.all()
        self.assertEqual(4, form_logics.count())
        form_logic_2 = form_logics.filter(form=imported_form).last()
        self.assertNotEqual(form_logic_2.pk, form_logic_pk)
        self.assertNotEqual(form_logic_2.uuid, str(form_logic.uuid))
        self.assertEqual(form_logic_2.form.pk, imported_form.pk)

    def test_import_no_backends(self):
        """
        explicitly test import/export of Form without backends as they use custom fields/choices
        """
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create()
        FormStepFactory.create(form=form, form_definition=form_definition)

        call_command("export", form.pk, self.filepath)

        form_definition.slug = "modified"
        form_definition.save()
        form.slug = "modified"
        form.save()

        call_command("import", import_file=self.filepath)

    def test_import_form_slug_already_exists(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product, slug="my-slug")
        form_definition = FormDefinitionFactory.create(
            configuration={"components": [{"key": "test-key", "type": "textfield"}]}
        )
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormLogicFactory.create(form=form)

        call_command("export", form.pk, self.filepath)

        call_command("import", import_file=self.filepath)

        imported_form = Form.objects.last()
        imported_form_step = imported_form.formstep_set.get()
        imported_form_definition = imported_form_step.form_definition

        # check we imported a new form
        self.assertNotEqual(form.pk, imported_form.pk)
        # check we added random hex chars
        self.assertRegex(imported_form.slug, r"^my-slug-[0-9a-f]{6}$")
        # check uuid mapping still works
        self.assertEqual(imported_form_definition.uuid, form_definition.uuid)

    def test_import_form_definition_slug_already_exists_configuration_duplicate(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create(
            configuration={"components": [{"key": "test-key", "type": "textfield"}]}
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        call_command("export", form.pk, self.filepath)

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        call_command("import", import_file=self.filepath)

        forms = Form.objects.all()
        imported_form = forms.last()
        self.assertEqual(forms.count(), 2)
        self.assertNotEqual(imported_form.pk, form_pk)
        self.assertNotEqual(imported_form.uuid, form.uuid)
        self.assertEqual(imported_form.active, False)
        self.assertEqual(imported_form.registration_backend, form.registration_backend)
        self.assertEqual(imported_form.name, form.name)
        self.assertEqual(imported_form.internal_name, form.internal_name)
        self.assertIsNone(imported_form.product)
        self.assertEqual(imported_form.slug, old_form_slug)

        form_definitions = FormDefinition.objects.all()
        fd2 = form_definitions.last()
        self.assertEqual(form_definitions.count(), 1)
        self.assertEqual(fd2.pk, form_definition_pk)
        self.assertEqual(fd2.uuid, form_definition.uuid)
        self.assertEqual(fd2.configuration, form_definition.configuration)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.internal_name, form_definition.internal_name)
        self.assertEqual(fd2.slug, form_definition.slug)

        form_steps = FormStep.objects.all()
        fs2 = form_steps.get(form=imported_form)
        self.assertEqual(form_steps.count(), 2)
        self.assertNotEqual(fs2.pk, form_step_pk)
        self.assertNotEqual(fs2.uuid, form_step.uuid)
        self.assertEqual(fs2.form.pk, imported_form.pk)
        self.assertEqual(fs2.form_definition.pk, fd2.pk)
        self.assertEqual(fs2.order, form_step.order)

        form_logics = FormLogic.objects.all()
        form_logic_2 = form_logics.filter(form=imported_form).last()
        self.assertEqual(form_logics.count(), 2)
        self.assertNotEqual(form_logic_2.pk, form_logic_pk)
        self.assertEqual(imported_form.pk, form_logic_2.form.pk)

    def test_import_form_definition_slug_already_exists_configuration_different(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create(
            configuration={"components": [{"key": "test-key", "type": "textfield"}]}
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        call_command("export", form.pk, self.filepath)

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        old_fd_config = form_definition.configuration
        form_definition.configuration = {"foo": ["bar"]}
        form_definition.save()

        call_command("import", import_file=self.filepath)

        forms = Form.objects.all()
        imported_form = forms.last()
        self.assertEqual(forms.count(), 2)
        self.assertNotEqual(imported_form.pk, form_pk)
        self.assertNotEqual(imported_form.uuid, form.uuid)
        self.assertEqual(imported_form.active, False)
        self.assertEqual(imported_form.registration_backend, form.registration_backend)
        self.assertEqual(imported_form.name, form.name)
        self.assertEqual(imported_form.internal_name, form.internal_name)
        self.assertIsNone(imported_form.product)
        self.assertEqual(imported_form.slug, old_form_slug)

        form_definitions = FormDefinition.objects.all()
        fd2 = form_definitions.last()
        self.assertEqual(form_definitions.count(), 2)
        self.assertNotEqual(fd2.pk, form_definition_pk)
        self.assertNotEqual(fd2.uuid, form_definition.uuid)
        self.assertEqual(fd2.configuration, old_fd_config)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.internal_name, form_definition.internal_name)
        self.assertEqual(fd2.slug, f"{form_definition.slug}-2")

        form_steps = FormStep.objects.all()
        fs2 = form_steps.get(form=imported_form)
        self.assertEqual(form_steps.count(), 2)
        self.assertNotEqual(fs2.pk, form_step_pk)
        self.assertNotEqual(fs2.uuid, form_step.uuid)
        self.assertEqual(fs2.form.pk, imported_form.pk)
        self.assertEqual(fs2.form_definition.pk, fd2.pk)
        self.assertEqual(fs2.order, form_step.order)

        form_logics = FormLogic.objects.all()
        form_logic_2 = form_logics.filter(form=imported_form).last()
        self.assertEqual(form_logics.count(), 2)
        self.assertNotEqual(form_logic_2.pk, form_logic_pk)
        self.assertEqual(imported_form.pk, form_logic_2.form.pk)

    def test_import_form_with_category(self):
        """
        Assert that the category reference is ignored during import.

        There are no guarantees that the categories on environment 1 are identical
        to the categories on environment two, so we don't do any guessing. Category
        names are also not unique, as the whole tree structure allows for duplicate
        names in different contexts. This makes it impossible to match a category
        by ID, name or even the path in the tree.

        Therefore, imported forms are always assigned to "no category".
        """
        category = CategoryFactory.create()
        form = FormFactory.create(category=category)
        call_command("export", form.pk, self.filepath)
        # delete the data to mimic an environment where category/form don't exist
        form.delete()
        category.delete()

        call_command("import", import_file=self.filepath)

        form = Form.objects.get()
        self.assertIsNone(form.category)

    @freeze_time()  # export metadata contains a timestamp
    def test_roundtrip_a_translated_form(self):
        self.maxDiff = None
        TranslatedFormFactory = make_translated(FormFactory)
        TranslatedFormDefinitionFactory = make_translated(FormDefinitionFactory)
        TranslatedFormStepFactory = make_translated(FormStepFactory)
        TranslatedConfirmationEmailTemplateFactory = make_translated(
            ConfirmationEmailTemplateFactory
        )
        other_language = "en"

        form: Form
        form_definition: FormDefinition
        form_step: FormStep
        email_template: ConfirmationEmailTemplate

        form = TranslatedFormFactory.create(
            _language=other_language,
            translation_enabled=True,
            name="Some form name translation",
            submission_confirmation_template="Some submission confirmation template translation",
            begin_text="Some begin text translation",
            previous_text="Some previous text translation",
            change_text="Some change text translation",
            confirm_text="Some confirm text translation",
            explanation_template="Some explanations template",
        )

        # set required untranslated string
        form.name = "Untranslated form name"
        form.submission_confirmation_template = (
            "Untranslated submission confirmation template"
        )
        form.begin_text = "Untranslated begin text"
        form.previous_text = "Untranslated previous text"
        form.change_text = "Untranslated change text"
        form.confirm_text = "Untranslated confirm text"
        form.explanation_template = "Some explanations template"
        form.save()

        email_template = TranslatedConfirmationEmailTemplateFactory.build(
            _language=other_language,
            form=form,
            subject="Some confirmation email subject translation",
            content=dedent(
                """
                Some confirmation email content translation with the obligatory
                {% appointment_information %}
                {% payment_information %}
                """
            ).strip(),
        )
        email_template.subject = "Untranslated confirmation email subject"
        email_template.content = dedent(
            """
            Untranslated confirmation email content with the obligatory
            {% appointment_information %}
            {% payment_information %}
            """
        ).strip()
        email_template.save()

        form_definition = TranslatedFormDefinitionFactory.create(
            _language=other_language,
            name="Some form definition name translation",
        )
        form_definition.name = "Untranslated form definition name"
        form_definition.save()

        form_step = TranslatedFormStepFactory.build(
            _language=other_language,
            form=form,
            form_definition=form_definition,
            previous_text="Some previous step text translation",
            save_text="Some save step text translation",
            next_text="Some next step text translation",
        )
        form_step.previous_text = "Untranslated previous step text"
        form_step.save_text = "Untranslated save step text"
        form_step.next_text = "Untranslated next step text"
        form_step.save()

        original_json = form_to_json(form.pk)

        # roundtrip
        with translation.override(other_language):
            call_command("export", form.pk, self.filepath)
        # language switched back to default
        form.delete()
        form_definition.delete()
        form_step.delete()
        email_template.delete()
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(FormDefinition.objects.count(), 0)
        self.assertEqual(FormStep.objects.count(), 0)
        call_command("import", import_file=self.filepath)

        imported_form = Form.objects.get()
        imported_form_step = imported_form.formstep_set.select_related().get()

        # assert translations survived the import
        self.assertEqual(imported_form.name, "Untranslated form name")
        self.assertEqual(
            imported_form.submission_confirmation_template,
            "Untranslated submission confirmation template",
        )
        self.assertEqual(imported_form.begin_text, "Untranslated begin text")
        self.assertEqual(imported_form.previous_text, "Untranslated previous text")
        self.assertEqual(imported_form.change_text, "Untranslated change text")
        self.assertEqual(imported_form.confirm_text, "Untranslated confirm text")
        self.assertEqual(
            imported_form.explanation_template, "Some explanations template"
        )
        self.assertEqual(imported_form.name_en, "Some form name translation")
        self.assertEqual(
            imported_form.submission_confirmation_template_en,
            "Some submission confirmation template translation",
        )
        self.assertEqual(imported_form.begin_text_en, "Some begin text translation")
        self.assertEqual(
            imported_form.previous_text_en, "Some previous text translation"
        )
        self.assertEqual(imported_form.change_text_en, "Some change text translation")
        self.assertEqual(imported_form.confirm_text_en, "Some confirm text translation")
        self.assertEqual(
            imported_form.explanation_template_en, "Some explanations template"
        )

        self.assertEqual(
            imported_form_step.previous_text_en, "Some previous step text translation"
        )
        self.assertEqual(
            imported_form_step.save_text_en, "Some save step text translation"
        )
        self.assertEqual(
            imported_form_step.next_text_en, "Some next step text translation"
        )
        self.assertEqual(
            imported_form.confirmation_email_template.subject_en,
            "Some confirmation email subject translation",
        )
        self.assertEqual(
            imported_form.confirmation_email_template.content_en,
            dedent(
                """
                Some confirmation email content translation with the obligatory
                {% appointment_information %}
                {% payment_information %}
                """
            ).strip(),  # trailing newline
        )
        self.assertEqual(
            imported_form.confirmation_email_template.content,
            dedent(
                """
                Untranslated confirmation email content with the obligatory
                {% appointment_information %}
                {% payment_information %}
                """
            ).strip(),  # trailing newline
        )

        self.assertEqual(
            imported_form_step.form_definition.name, "Untranslated form definition name"
        )
        self.assertEqual(
            imported_form_step.form_definition.name_en,
            "Some form definition name translation",
        )
        self.assertEqual(form_step.previous_text, "Untranslated previous step text")
        self.assertEqual(form_step.save_text, "Untranslated save step text")
        self.assertEqual(form_step.next_text, "Untranslated next step text")

        # inspect the exported data structure, configs etc.
        imported_json = form_to_json(imported_form.pk)
        expected_differences = {
            "forms": [
                "uuid",  # import gets assigned a new one
                "url",  # contains uuid
                "active",  # import gets set to inactive
                "category",  # gets unset
                "steps",  # duplicated in formSteps
            ],
            "formSteps": [
                "form_definition",  # is a url with uuid
                "uuid",
                "url",
            ],
            "formDefinitions": [
                "uuid",
                "url",
            ],
        }

        def remove_expected_differences(part: str, obj1: dict, obj2: dict) -> None:
            for field in expected_differences.get(part, ()):
                del obj1[field]
                del obj2[field]

        def head(v: list | dict) -> dict | None:
            "Return first dict in the list"
            if isinstance(v, dict):  # _meta is already an object
                return v
            return None if not v else v[0]

        # assert JSON is still equivalent
        for part, json_string in original_json.items():
            with self.subTest(part=part):
                expected_data = json.loads(json_string)
                imported_data = json.loads(imported_json[part])
                # they should have the same number of elements/keys to start with
                self.assertEqual(len(imported_data), len(expected_data))

                expected = head(expected_data)
                imported_value = head(imported_data)

                remove_expected_differences(part, expected, imported_value)
                self.assertEqual(imported_value, expected)

    @tag("gh-2432")
    def test_import_form_with_disable_step_logic(self):
        resources = {
            "forms": [
                {
                    "active": True,
                    "authentication_backends": [],
                    "is_deleted": False,
                    "login_required": False,
                    "maintenance_mode": False,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "product": None,
                    "show_progress_indicator": True,
                    "slug": "auth-plugins",
                    "url": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                }
            ],
            "formSteps": [
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "form_definition": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                    "index": 0,
                    "slug": "test-step-1",
                    "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                },
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "form_definition": "http://testserver/api/v2/form-definitions/a54864c6-c460-48bd-a520-eced60ffb209",
                    "index": 1,
                    "slug": "test-step-2",
                    "uuid": "a54864c6-c460-48bd-a520-eced60ffb209",
                },
            ],
            "formDefinitions": [
                {
                    "configuration": {
                        "components": [
                            {
                                "key": "radio",
                                "type": "radio",
                                "values": [
                                    {"label": "yes", "value": "yes"},
                                    {"label": "no", "value": "no"},
                                ],
                            },
                        ]
                    },
                    "name": "Def 1 - With condition",
                    "slug": "test-definition-1",
                    "url": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                    "uuid": "f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                },
                {
                    "configuration": {"components": []},
                    "name": "Def 2 - to be marked as not applicable",
                    "slug": "test-definition-2",
                    "url": "http://testserver/api/v2/form-definitions/a54864c6-c460-48bd-a520-eced60ffb209",
                    "uuid": "a54864c6-c460-48bd-a520-eced60ffb209",
                },
            ],
            "formLogic": [
                {
                    "actions": [
                        {
                            "action": {"type": "step-not-applicable"},
                            # In versions <= 2.0, we used the url of the form step, but this was replaced with the UUID
                            "form_step": "http://127.0.0.1:8999/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2/steps/a54864c6-c460-48bd-a520-eced60ffb209",
                        }
                    ],
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "json_logic_trigger": {"==": [{"var": "radio"}, "ja"]},
                    "uuid": "b92342be-05e0-4070-b2cc-1b88af472091",
                }
            ],
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        call_command("import", import_file=self.filepath)

        self.assertTrue(Form.objects.filter(slug="auth-plugins").exists())
