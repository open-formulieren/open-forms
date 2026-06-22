import json
import tempfile
import zipfile
from pathlib import Path
from shutil import rmtree
from textwrap import dedent
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase, override_settings, tag
from django.utils import translation

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from openforms.config.constants import UploadFileType
from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import ThemeFactory
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.products.tests.factories import ProductFactory
from openforms.registrations.contrib.objects_api.config import (
    ObjectsAPIOptionsSerializer,
)
from openforms.registrations.contrib.objects_api.constants import (
    PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER,
)
from openforms.registrations.contrib.objects_api.typing import (
    RegistrationOptionsV2 as ObjectsRegistrationOptionsV2,
)
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ...authentication.tests.factories import AttributeGroupFactory
from ..constants import EXPORT_META_KEY
from ..disable_next_import_conversion import add_form_step_uuid_to_disable_next_actions
from ..models import (
    Form,
    FormAuthenticationBackend,
    FormDefinition,
    FormLogic,
    FormRegistrationBackend,
    FormStep,
    FormVariable,
)
from ..utils import export_form, form_to_json, import_form
from .factories import (
    CategoryFactory,
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)

PATH = Path(__file__).parent


class TempdirMixin:
    """
    Set up temporary directories for export files to avoid race conditions.

    When running tests in parallel, multiple processes can be manipulating the filepath
    where the export file ends up, and if these directories are fixed/not guaranteed
    to be isolated from each other, one test cleanup can be deleting the file to be
    used by another, or worse, the wrong content is set up and the tests are flaky.
    """

    def setUp(self):
        super().setUp()  # pyright: ignore[reportAttributeAccessIssue]

        test_dir = Path(tempfile.mkdtemp())

        self.filepath = test_dir / "export_test.zip"
        self.addCleanup(  # pyright: ignore[reportAttributeAccessIssue]
            lambda: self.filepath.unlink(missing_ok=True)
        )
        self.addCleanup(  # pyright: ignore[reportAttributeAccessIssue]
            lambda: rmtree(test_dir, ignore_errors=True)
        )


class ImportExportTests(TempdirMixin, TestCase):
    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_export(self):
        form, _ = FormFactory.create_batch(2, authentication_backend="demo")
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormStepFactory.create()
        FormLogicFactory.create(
            form=form,
            actions=[
                {
                    "component": "test_component",
                    "action": {
                        "type": "set-registration-backend",
                        "value": "foo",
                    },
                }
            ],
        )
        FormVariableFactory.create(
            form=form, source=FormVariableSources.user_defined, key="test-user-defined"
        )

        export_form(form.pk, archive_name=self.filepath)

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
            self.assertEqual(
                forms[0]["auth_backends"],
                [
                    {
                        "backend": "demo",
                        "options": {},
                    }
                ],
            )
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
                {"type": "set-registration-backend", "value": "foo"},
                form_logic[0]["actions"][0]["action"],
            )
            self.assertIn(str(form.uuid), form_logic[0]["form"])

            form_variables = json.loads(f.read("formVariables.json"))
            # Only user defined form variables are included in the export
            self.assertEqual(len(form_variables), 1)
            self.assertEqual(
                FormVariableSources.user_defined, form_variables[0]["source"]
            )

    @tag("gh-1906")
    def test_export_reusable_form_definition_uuid_already_exists(self):
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "test-key",
                        "label": "test-key",
                        "file": {"type": []},
                        "filePattern": "",
                    }
                ]
            },
            is_reusable=True,
        )
        FormStepFactory.create(form=form, form_definition=form_definition)

        export_form(form.pk, archive_name=self.filepath)

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

    def test_import(self):
        product = ProductFactory.create()
        merchant = WorldlineMerchantFactory.create()
        form = FormFactory.create(
            product=product,
            authentication_backend="digid",
            payment_backend="worldline",
            payment_backend_options={"merchant": merchant.pspid},
        )
        FormRegistrationBackendFactory.create(
            form=form,
            backend="email",
            options={
                "to_emails": ["foo@bar.baz"],
                "attach_files_to_email": None,
            },
        )
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key",
                        "label": "test-key",
                    }
                ]
            }
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        FormVariableFactory.create(
            form=form, user_defined=True, key="test-user-defined"
        )

        # fetch configurations are not exported (yet)
        # but shouldn't break export - import
        fetch_config = ServiceFetchConfigurationFactory.create()
        far_fetched = FormVariableFactory.create(
            form=form,
            user_defined=True,
            name="far_fetched",
            key="farFetched",
            service_fetch_configuration=fetch_config,
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!": {"var": "farFetched"}},
            is_advanced=True,
            actions=[
                {
                    "action": {"type": "fetch-from-service", "value": ""},
                    "variable": "farFetched",
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

        export_form(form.pk, archive_name=self.filepath)

        # attempt to break ForeignKey constraint
        far_fetched.delete()
        fetch_config.delete()

        # check that the form definition is updated with the import data
        old_form_definition_slug = form_definition.slug
        form_definition.slug = "modified"
        form_definition.save()

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        import_form(import_file=self.filepath)

        forms = Form.objects.all()
        imported_form = forms.last()

        # The backend_registration id and form are expected to be different,
        # compare only the values that should be the same
        backend_registrations = list(
            form.registration_backends.values("key", "name", "backend", "options")
        )
        imported_backend_registrations = list(
            imported_form.registration_backends.values(
                "key", "name", "backend", "options"
            )
        )

        self.assertEqual(forms.count(), 2)
        self.assertNotEqual(imported_form.pk, form_pk)
        self.assertNotEqual(imported_form.uuid, str(form.uuid))
        self.assertEqual(imported_form.active, False)
        self.assertEqual(
            imported_form.registration_backends.count(),
            form.registration_backends.count(),
        )
        self.assertQuerySetEqual(backend_registrations, imported_backend_registrations)
        self.assertEqual(imported_form.name, form.name)
        self.assertIsNone(imported_form.product)
        self.assertEqual(imported_form.slug, old_form_slug)
        self.assertEqual(imported_form.auth_backends.count(), 1)
        self.assertEqual(imported_form.auth_backends.get().backend, "digid")
        self.assertEqual(imported_form.payment_backend, "worldline")
        self.assertEqual(
            imported_form.payment_backend_options,
            {
                "merchant": merchant.pspid,
                "variant": "",
                "descriptor_template": "",
            },
        )

        form_definitions = FormDefinition.objects.order_by("pk")
        self.assertEqual(len(form_definitions), 2)
        fd2 = form_definitions[1]
        self.assertNotEqual(fd2.pk, form_definition_pk)
        self.assertNotEqual(fd2.uuid, form_definition.uuid)
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

        # assert 3 user_defined_vars
        # 1. original test-user-defined
        # 2. imported test-user-defined
        # 3. imported far_fetched (but without service_fetch_configuration)
        self.assertEqual(user_defined_vars.count(), 3)

        form_logics = FormLogic.objects.all()
        self.assertEqual(4, form_logics.count())
        form_logic_2 = form_logics.filter(form=imported_form).last()
        self.assertNotEqual(form_logic_2.pk, form_logic_pk)
        self.assertNotEqual(form_logic_2.uuid, str(form_logic.uuid))
        self.assertEqual(form_logic_2.form.pk, imported_form.pk)

    @tag("gh-3379")
    def test_import_2_1_3_export_does_not_fail(self):
        import_form(import_file=PATH / "data/smol.zip")
        self.assertTrue(Form.objects.filter(name="Smol").exists())

    def test_import_no_backends(self):
        """
        explicitly test import/export of Form without backends as they use custom fields/choices
        """
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create()
        FormStepFactory.create(form=form, form_definition=form_definition)

        export_form(form.pk, archive_name=self.filepath)

        form_definition.slug = "modified"
        form_definition.save()
        form.slug = "modified"
        form.save()

        import_form(import_file=self.filepath)

    def test_import_form_slug_already_exists(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product, slug="my-slug")
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key",
                        "label": "test-key",
                    }
                ]
            },
            is_reusable=True,
        )
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormLogicFactory.create(form=form)

        export_form(form.pk, archive_name=self.filepath)

        import_form(import_file=self.filepath)

        imported_form = Form.objects.last()
        imported_form_step = imported_form.formstep_set.get()
        imported_form_definition = imported_form_step.form_definition

        # check we imported a new form
        self.assertNotEqual(form.pk, imported_form.pk)
        # check we added random hex chars
        self.assertRegex(imported_form.slug, r"^my-slug-[0-9a-f]{6}$")
        # check uuid mapping still works
        self.assertEqual(imported_form_definition.uuid, form_definition.uuid)

    def test_import_form_definition_uuid_already_exists_configuration_duplicate(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key",
                        "label": "test-key",
                    }
                ]
            },
            is_reusable=True,
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        export_form(form.pk, archive_name=self.filepath)

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        import_form(import_file=self.filepath)

        forms = Form.objects.all()
        imported_form = forms.last()

        # The backend_registration id and form are expected to be different,
        # compare only the values that should be the same
        backend_registrations = list(
            form.registration_backends.values("key", "name", "backend", "options")
        )
        imported_backend_registrations = list(
            imported_form.registration_backends.values(
                "key", "name", "backend", "options"
            )
        )

        self.assertEqual(forms.count(), 2)
        self.assertNotEqual(imported_form.pk, form_pk)
        self.assertNotEqual(imported_form.uuid, form.uuid)
        self.assertEqual(imported_form.active, False)
        self.assertEqual(
            imported_form.registration_backends.count(),
            form.registration_backends.count(),
        )
        self.assertQuerySetEqual(backend_registrations, imported_backend_registrations)
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

    def test_import_form_definition_uuid_already_exists_configuration_different(self):
        product = ProductFactory.create()
        form = FormFactory.create(product=product)
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test-key",
                        "label": "test-key",
                    }
                ]
            },
            is_reusable=True,  # only re-usable FDs may be related to multiple forms
        )
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_logic = FormLogicFactory.create(form=form)

        form_pk, form_definition_pk, form_step_pk, form_logic_pk = (
            form.pk,
            form_definition.pk,
            form_step.pk,
            form_logic.pk,
        )

        export_form(form.pk, archive_name=self.filepath)

        old_form_slug = form.slug
        form.slug = "modified"
        form.save()

        old_fd_config = form_definition.configuration
        form_definition.configuration = {"foo": ["bar"]}
        form_definition.save()

        import_form(import_file=self.filepath)

        forms = Form.objects.all()
        imported_form = forms.last()
        # The backend_registration id and form are expected to be different,
        # compare only the values that should be the same
        backend_registrations = list(
            form.registration_backends.values("key", "name", "backend", "options")
        )
        imported_backend_registrations = list(
            imported_form.registration_backends.values(
                "key", "name", "backend", "options"
            )
        )

        self.assertEqual(forms.count(), 2)
        self.assertNotEqual(imported_form.pk, form_pk)
        self.assertNotEqual(imported_form.uuid, form.uuid)
        self.assertEqual(imported_form.active, False)
        self.assertEqual(
            imported_form.registration_backends.count(),
            form.registration_backends.count(),
        )
        self.assertEqual(imported_backend_registrations, backend_registrations)
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

    @tag("gh-1906")
    def test_import_reusable_form_definition_uuid_already_exists(self):
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "test-key",
                        "label": "test-key",
                        "file": {"type": []},
                        "filePattern": "",
                    }
                ]
            },
            is_reusable=True,
        )
        FormStepFactory.create(form=form, form_definition=form_definition)

        export_form(form.pk, archive_name=self.filepath)

        import_form(import_file=self.filepath)

        form_definitions = FormDefinition.objects.all()
        fd2 = form_definitions.last()
        self.assertEqual(form_definitions.count(), 1)
        self.assertEqual(fd2.pk, form_definition.pk)
        self.assertEqual(fd2.uuid, form_definition.uuid)
        self.assertEqual(fd2.configuration, form_definition.configuration)
        self.assertEqual(fd2.login_required, form_definition.login_required)
        self.assertEqual(fd2.name, form_definition.name)
        self.assertEqual(fd2.internal_name, form_definition.internal_name)
        self.assertEqual(fd2.slug, form_definition.slug)

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
        export_form(form.pk, archive_name=self.filepath)
        # delete the data to mimic an environment where category/form don't exist
        form.delete()
        category.delete()

        import_form(import_file=self.filepath)

        form = Form.objects.get()
        self.assertIsNone(form.category)

    @freeze_time()  # export metadata contains a timestamp
    def test_roundtrip_a_translated_form(self):
        self.maxDiff = None

        form: Form
        form_definition: FormDefinition
        form_step: FormStep
        email_template: ConfirmationEmailTemplate

        form = FormFactory.create(
            # set required untranslated string
            name="Untranslated form name",
            submission_confirmation_template="Untranslated submission confirmation template",
            begin_text="Untranslated begin text",
            previous_text="Untranslated previous text",
            change_text="Untranslated change text",
            confirm_text="Untranslated confirm text",
            explanation_template="Some explanations template",
            # English translations
            translation_enabled=True,
            name_en="Some form name translation",
            submission_confirmation_template_en="Some submission confirmation template translation",
            begin_text_en="Some begin text translation",
            previous_text_en="Some previous text translation",
            change_text_en="Some change text translation",
            confirm_text_en="Some confirm text translation",
            explanation_template_en="Some explanations template",
        )

        email_template = ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Untranslated confirmation email subject",
            content=dedent(
                """
                        Untranslated confirmation email content with the obligatory
                        {% cosign_information %}
                        {% appointment_information %}
                        {% payment_information %}
                        """
            ).strip(),
            subject_en="Some confirmation email subject translation",
            content_en=dedent(
                """
                Some confirmation email content translation with the obligatory
                {% cosign_information %}
                {% appointment_information %}
                {% payment_information %}
                """
            ).strip(),
        )

        form_definition = FormDefinitionFactory.create(
            name="Untranslated form definition name",
            name_en="Some form definition name translation",
        )

        form_step = FormStepFactory.create(
            form=form,
            form_definition=form_definition,
            previous_text="Untranslated previous step text",
            save_text="Untranslated save step text",
            next_text="Untranslated next step text",
            previous_text_en="Some previous step text translation",
            save_text_en="Some save step text translation",
            next_text_en="Some next step text translation",
        )

        original_json = form_to_json(form.pk)

        # roundtrip
        with translation.override("en"):
            export_form(form.pk, archive_name=self.filepath)
        # language switched back to default
        form.delete()
        form_definition.delete()
        form_step.delete()
        email_template.delete()
        self.assertEqual(Form.objects.count(), 0)
        self.assertEqual(FormDefinition.objects.count(), 0)
        self.assertEqual(FormStep.objects.count(), 0)
        import_form(import_file=self.filepath)

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
                {% cosign_information %}
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
                {% cosign_information %}
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
                                "type": "radio",
                                "key": "radio",
                                "label": "radio",
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
                            "form_step_uuid": "a54864c6-c460-48bd-a520-eced60ffb209",
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

        import_form(import_file=self.filepath)

        self.assertTrue(Form.objects.filter(slug="auth-plugins").exists())

    @tag("sentry-334878")
    @patch(
        "openforms.formio.components.vanilla.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            form_upload_default_file_types=[UploadFileType.all]
        ),
    )
    def test_export_with_filetype_information(self, m_get_solo):
        component = {
            "type": "file",
            "key": "fileTest",
            "label": "fileTest",
            "url": "",
            "useConfigFiletypes": True,
            "filePattern": "*",
            "file": {"type": []},
        }

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={"components": [component]},
        )

        export_data = form_to_json(form.pk)

        self.assertIsInstance(export_data, dict)

    def test_import_applies_converters(self):
        def add_foo(component):
            component["foo"] = "bar"
            return True

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "textfield",
                    },
                    {
                        "type": "email",
                        "key": "nottextfield",
                        "label": "nottextfield",
                    },
                ]
            },
        )
        export_form(form.pk, archive_name=self.filepath)

        converters = {"textfield": {"add_foo": add_foo}}
        with patch("openforms.forms.utils.CONVERTERS", new=converters):
            import_form(import_file=self.filepath)

        imported_form = Form.objects.exclude(pk=form.pk).get()
        fd = imported_form.formstep_set.get().form_definition
        comp1, comp2 = fd.configuration["components"]

        self.assertIn("foo", comp1)
        self.assertNotIn("foo", comp2)

    def test_rountrip_form_with_theme_override(self):
        theme = ThemeFactory.create()
        form = FormFactory.create(generate_minimal_setup=True, theme=theme)
        export_form(form.pk, archive_name=self.filepath)

        # run the import again
        import_form(import_file=self.filepath)

        imported_form = Form.objects.exclude(pk=form.pk).get()
        self.assertIsNone(imported_form.theme)

    @tag("gh-3975")
    def test_import_form_with_old_service_fetch_config(self):
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
                    "slug": "old-service-fetch-config",
                    "url": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                }
            ],
            "formSteps": [
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "form_definition": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                    "index": 0,
                    "slug": "test-step",
                    "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                }
            ],
            "formDefinitions": [
                {
                    "configuration": {"components": []},
                    "name": "A definition",
                    "slug": "test-definition",
                    "url": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                    "uuid": "f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                },
            ],
            "formLogic": [
                {
                    "actions": [
                        {
                            "action": {
                                "type": "fetch-from-service",
                                "value": "1",
                            },  # Old service fetch format
                            "variable": "aVariable",
                            "component": "",
                            "form_step": "",
                            "form_step_uuid": None,
                        }
                    ],
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "json_logic_trigger": {"!!": [True]},
                    "uuid": "b92342be-05e0-4070-b2cc-1b88af472091",
                    "order": 0,
                    "is_advanced": True,
                }
            ],
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        rule = FormLogic.objects.get(form__slug="old-service-fetch-config", order=0)
        self.assertEqual(rule.actions[0]["action"]["value"], "")

    @tag("gh-3964")
    def test_import_form_with_old_simple_conditionals_with_numbers(self):
        """
        Test for importing a form where simple conditionals in the logic that use the values of
        number or currency components: {"eq": "0.555", "show": True, "when": "number"}
        but compare the values to a string ("eq": "0.555") instead of a number ("eq": 0.555).
        """
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
                    "slug": "old-service-fetch-config",
                    "url": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                }
            ],
            "formSteps": [
                {
                    "form": "http://testserver/api/v2/forms/324cadce-a627-4e3f-b117-37ca232f16b2",
                    "form_definition": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                    "index": 0,
                    "slug": "test-step",
                    "uuid": "3ca01601-cd20-4746-bce5-baab47636823",
                }
            ],
            "formDefinitions": [
                {
                    "configuration": {
                        "components": [
                            {"key": "number", "type": "number", "label": "Number"},
                            {
                                "key": "currency",
                                "type": "currency",
                                "label": "Currency",
                            },
                            {
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Text Field",
                            },
                            {
                                "key": "textArea1",
                                "type": "textarea",
                                "label": "Text Area 1",
                                "conditional": {
                                    "eq": "0",
                                    "show": True,
                                    "when": "number",
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea2",
                                "type": "textarea",
                                "label": "Text Area 2",
                                "conditional": {
                                    "eq": "0.555",
                                    "show": True,
                                    "when": "number",
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea3",
                                "type": "textarea",
                                "label": "Text Area 3",
                                "conditional": {"eq": "", "show": None, "when": ""},
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea4",
                                "type": "textarea",
                                "label": "Text Area 4",
                                "conditional": {
                                    "when": "currency",
                                    "eq": "0.55",
                                    "show": True,
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea5",
                                "type": "textarea",
                                "label": "Text Area 5",
                                "conditional": {
                                    "eq": "1.00",
                                    "when": "currency",
                                    "show": True,
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "textArea6",
                                "type": "textarea",
                                "label": "Text Area 6",
                                "conditional": {
                                    "eq": "1.00",
                                    "when": "textfield",
                                    "show": True,
                                },
                                "clearOnHide": True,
                            },
                            {
                                "key": "repeatingGroup",
                                "type": "editgrid",
                                "label": "Repeating group",
                                "groupLabel": "Item",
                                "components": [
                                    {
                                        "key": "textArea7",
                                        "type": "textarea",
                                        "label": "Text Area 7",
                                        "conditional": {
                                            "eq": "0",
                                            "show": True,
                                            "when": "number",
                                        },
                                        "clearOnHide": True,
                                    },
                                ],
                            },
                            {
                                "key": "textArea8",
                                "type": "textarea",
                                "label": "Text Area 8",
                                "conditional": {
                                    "eq": 0,
                                    "show": True,
                                    "when": "number",
                                },
                                "clearOnHide": True,
                            },
                        ]
                    },
                    "name": "A definition",
                    "slug": "test-definition",
                    "url": "http://testserver/api/v2/form-definitions/f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                    "uuid": "f0dad93b-333b-49af-868b-a6bcb94fa1b8",
                },
            ],
            "formLogic": [],
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        form_definition = FormDefinition.objects.get(slug="test-definition")
        fixed_components = form_definition.configuration["components"]

        self.assertIsInstance(fixed_components[3]["conditional"]["eq"], int)
        self.assertIsInstance(fixed_components[4]["conditional"]["eq"], float)
        self.assertNotIn("eq", fixed_components[5]["conditional"])
        self.assertIsInstance(fixed_components[6]["conditional"]["eq"], float)
        self.assertIsInstance(fixed_components[7]["conditional"]["eq"], float)
        self.assertIsInstance(fixed_components[8]["conditional"]["eq"], str)
        self.assertIsInstance(
            fixed_components[9]["components"][0]["conditional"]["eq"], int
        )
        self.assertIsInstance(fixed_components[10]["conditional"]["eq"], int)

    def test_import_applies_converters_map_component_interactions(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "mapWithoutInteractions",
                        "type": "map",
                        "label": "Map",
                        "useConfigDefaultMapSettings": True,
                    },
                    {
                        "key": "mapWithInteractions",
                        "type": "map",
                        "label": "Map",
                        "useConfigDefaultMapSettings": True,
                        "interactions": {
                            "marker": False,
                            "polygon": True,
                            "polyline": True,
                        },
                    },
                ]
            },
        )
        export_form(form.pk, archive_name=self.filepath)
        import_form(import_file=self.filepath)

        imported_form = Form.objects.exclude(pk=form.pk).get()
        fd = imported_form.formstep_set.get().form_definition

        self.assertEqual(
            fd.configuration["components"],
            [
                {
                    "key": "mapWithoutInteractions",
                    "type": "map",
                    "label": "Map",
                    "useConfigDefaultMapSettings": True,
                    "interactions": {
                        "marker": True,
                        "polygon": False,
                        "polyline": False,
                    },
                },
                {
                    "key": "mapWithInteractions",
                    "type": "map",
                    "label": "Map",
                    "useConfigDefaultMapSettings": True,
                    "interactions": {
                        "marker": False,
                        "polygon": True,
                        "polyline": True,
                    },
                },
            ],
        )

    def test_import_form_with_old_authentication_backends(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "authentication_backends": ["digid", "demo"],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        imported_form = Form.objects.get(slug="test-form")
        authentication_backends = imported_form.auth_backends.all()

        self.assertEqual(len(authentication_backends), 2)

        self.assertEqual(authentication_backends[0].backend, "digid")
        self.assertEqual(authentication_backends[0].form, imported_form)
        self.assertEqual(authentication_backends[0].options, {"loa": ""})

        self.assertEqual(authentication_backends[1].backend, "demo")
        self.assertEqual(authentication_backends[1].form, imported_form)
        self.assertEqual(authentication_backends[1].options, None)

    def test_import_form_with_old_authentication_backend_options(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "authentication_backend_options": {
                        "digid": {
                            "loa": DigiDAssuranceLevels.substantial,
                            "unknown_attribute": "will be removed",
                        }
                    },
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        imported_form = Form.objects.get(slug="test-form")
        form_authentication_backend = FormAuthenticationBackend.objects.filter(
            form=imported_form
        ).first()

        # Assert that there is a FormAuthenticationBackend for the form, with the correct
        # plugin and configuration
        self.assertIsNotNone(form_authentication_backend)
        self.assertEqual(form_authentication_backend.backend, "digid")
        # Unknown attributes should be removed
        self.assertEqual(
            form_authentication_backend.options,
            {"loa": DigiDAssuranceLevels.substantial},
        )

    def test_import_form_with_old_authentication_backends_and_authentication_backend_options(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "authentication_backends": ["demo"],
                    "authentication_backend_options": {
                        "digid": {
                            "loa": DigiDAssuranceLevels.substantial,
                            "unknown_attribute": "will be removed",
                        }
                    },
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        imported_form = Form.objects.get(slug="test-form")
        authentication_backends = imported_form.auth_backends.all()

        self.assertEqual(len(authentication_backends), 2)

        self.assertEqual(authentication_backends[0].backend, "demo")
        self.assertEqual(authentication_backends[0].form, imported_form)
        self.assertEqual(authentication_backends[0].options, None)

        self.assertEqual(authentication_backends[1].backend, "digid")
        self.assertEqual(authentication_backends[1].form, imported_form)
        self.assertEqual(
            authentication_backends[1].options,
            {
                "loa": DigiDAssuranceLevels.substantial,
            },
        )

    def test_import_form_with_old_and_new_authentication_backends_will_merge_both_together(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "auth_backends": [
                        {
                            "backend": "demo",
                            "options": None,
                        },
                        {
                            "backend": "digid",
                            "options": {
                                "loa": DigiDAssuranceLevels.substantial,
                            },
                        },
                        {
                            "backend": "eherkenning",
                            "options": None,
                        },
                    ],
                    "authentication_backends": ["demo", "digid", "digid_oidc"],
                    "authentication_backend_options": {
                        "demo": {
                            "some_custom_attribute": "will be added",
                        },
                        "digid": {
                            "loa": DigiDAssuranceLevels.high,
                        },
                    },
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        imported_form = Form.objects.get(slug="test-form")
        authentication_backends = imported_form.auth_backends.all()

        self.assertEqual(len(authentication_backends), 4)

        # Because the demo `auth_backends` plugin options where undefined, the config was
        # supplied by `authentication_backend_options`
        self.assertEqual(authentication_backends[0].backend, "demo")
        self.assertEqual(authentication_backends[0].form, imported_form)
        self.assertEqual(
            authentication_backends[0].options,
            {
                "some_custom_attribute": "will be added",
            },
        )

        # Config defined in `auth_backends` plugins will be used in favor of
        # `authentication_backend_options`
        self.assertEqual(authentication_backends[1].backend, "digid")
        self.assertEqual(authentication_backends[1].form, imported_form)
        self.assertEqual(
            authentication_backends[1].options,
            {
                "loa": DigiDAssuranceLevels.substantial.value,
            },
        )

        # Plugins that exist in `auth_backends`, but not in `authentication_backends`,
        # will remain
        self.assertEqual(authentication_backends[2].backend, "eherkenning")
        self.assertEqual(authentication_backends[2].form, imported_form)
        self.assertEqual(authentication_backends[2].options, None)

        # Plugins that exist in `authentication_backends`, but not in `auth_backends`,
        # will be added
        self.assertEqual(authentication_backends[3].backend, "digid_oidc")
        self.assertEqual(authentication_backends[3].form, imported_form)
        self.assertEqual(authentication_backends[3].options, None)

    def test_import_form_with_auth_backends(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "auth_backends": [
                        {
                            "backend": "demo",
                        },
                        {
                            "backend": "digid",
                            "options": {
                                "loa": DigiDAssuranceLevels.substantial,
                                "unknown_attribute": "will be removed",
                            },
                        },
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        imported_form = Form.objects.get(slug="test-form")
        authentication_backends = imported_form.auth_backends.all()

        self.assertEqual(len(authentication_backends), 2)

        self.assertEqual(authentication_backends[0].backend, "demo")
        self.assertEqual(authentication_backends[0].form, imported_form)
        self.assertEqual(authentication_backends[0].options, None)

        self.assertEqual(authentication_backends[1].backend, "digid")
        self.assertEqual(authentication_backends[1].form, imported_form)
        self.assertEqual(
            authentication_backends[1].options,
            {
                "loa": DigiDAssuranceLevels.substantial,
            },
        )

    def test_import_form_with_missing_backend_in_auth_backends(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "auth_backends": [
                        {
                            "options": {
                                "loa": DigiDAssuranceLevels.substantial,
                                "unknown_attribute": "will be removed",
                            }
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        with self.assertRaises(ValidationError) as exc:
            import_form(import_file=self.filepath)

        error_detail = exc.exception.detail["auth_backends"][0]["backend"][0]

        self.assertEqual(error_detail.code, "required")

    def test_import_form_with_unknown_backend_in_auth_backends(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "auth_backends": [
                        {
                            "backend": "unknown_backend",
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        with self.assertRaises(ValidationError) as exc:
            import_form(import_file=self.filepath)

        error_detail = exc.exception.detail["auth_backends"][0]["backend"][0]

        self.assertEqual(error_detail.code, "invalid")

    def test_import_form_with_yivi_auth_backend(self):
        AttributeGroupFactory.create(
            name="known_attributes", uuid="a1c9df69-927c-4390-be26-f39daf107691"
        )
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "auth_backends": [
                        {
                            "backend": "yivi_oidc",
                            "options": {
                                "authentication_options": [
                                    "bsn",
                                    "kvk",
                                ],
                                "additional_attributes_groups": [
                                    "a1c9df69-927c-4390-be26-f39daf107691",
                                ],
                                "bsn_loa": DigiDAssuranceLevels.substantial,
                                "kvk_loa": AssuranceLevels.low,
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        imported_form = Form.objects.get(slug="test-form")
        authentication_backends = imported_form.auth_backends.all()
        assert len(authentication_backends) == 1

        auth_backend = authentication_backends[0]

        # Expect all authentication backend data to be imported
        self.assertEqual(auth_backend.backend, "yivi_oidc")
        self.assertEqual(
            auth_backend.options["bsn_loa"], DigiDAssuranceLevels.substantial
        )
        self.assertEqual(auth_backend.options["kvk_loa"], AssuranceLevels.low)
        self.assertEqual(auth_backend.options["authentication_options"], ["bsn", "kvk"])
        self.assertEqual(
            auth_backend.options["additional_attributes_groups"],
            ["a1c9df69-927c-4390-be26-f39daf107691"],
        )

    def test_import_form_with_yivi_auth_backend_with_known_old_additional_attributes_groups_reference_updates_options(
        self,
    ):
        AttributeGroupFactory.create(
            name="known_attributes", uuid="a1c9df69-927c-4390-be26-f39daf107691"
        )
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "auth_backends": [
                        {
                            "backend": "yivi_oidc",
                            "options": {
                                "authentication_options": [
                                    "bsn",
                                    "kvk",
                                ],
                                "additional_attributes_groups": [
                                    # The name of the previously defined attributeGroup
                                    "known_attributes",
                                ],
                                "bsn_loa": DigiDAssuranceLevels.substantial,
                                "kvk_loa": AssuranceLevels.low,
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        imported_form = Form.objects.get(slug="test-form")
        authentication_backends = imported_form.auth_backends.all()
        assert len(authentication_backends) == 1

        auth_backend = authentication_backends[0]

        self.assertEqual(auth_backend.backend, "yivi_oidc")
        self.assertEqual(
            auth_backend.options["additional_attributes_groups"],
            ["a1c9df69-927c-4390-be26-f39daf107691"],
        )

    def test_import_form_with_yivi_auth_backend_with_unknown_additional_attributes_groups_raises_exception(
        self,
    ):
        AttributeGroupFactory.create(
            name="some_known_scope", uuid="447aad2c-dc7d-4220-ba5c-dd15183c7a02"
        )
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "auth_backends": [
                        {
                            "backend": "yivi_oidc",
                            "options": {
                                "additional_attributes_groups": [
                                    # A known uuid
                                    "447aad2c-dc7d-4220-ba5c-dd15183c7a02",
                                    # An unknown/invalid uuid
                                    "86ed3db9-8aad-4d9d-a516-a4c3794ed036",
                                ]
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        with self.assertRaises(ValidationError) as exc:
            import_form(import_file=self.filepath)

        error_detail = exc.exception.detail["auth_backends"][0]["options"][
            "additional_attributes_groups"
        ][0]

        self.assertEqual(error_detail.code, "does_not_exist")

    def test_import_export_in_stuf_zds(self):
        """
        Test the old options are updated during export/import.
        """
        form = FormFactory.create()
        FormRegistrationBackend.objects.create(
            form=form,
            name="StUF-ZDS registration",
            key="stuf-zds-registration",
            backend="stuf-zds-create-zaak",
            options={
                "payment_status_update_mapping": [
                    {
                        "stuf_name": "payment_completed",
                        "form_variable": "payment_completed",
                    },
                    {"stuf_name": "payment_amount", "form_variable": "payment_amount"},
                    {
                        "stuf_name": "payment_public_order_ids",
                        "form_variable": "payment_public_order_ids",
                    },
                    {
                        "stuf_name": "provider_payment_ids",
                        "form_variable": "provider_payment_ids",
                    },
                ],
                "zds_zaaktype_code": "test",
                "zds_zaaktype_status_code": "",
                "zds_zaaktype_omschrijving": "",
                "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
                "zds_zaaktype_status_omschrijving": "",
                "zds_documenttype_omschrijving_inzending": "",
            },
        )

        export_form(form.pk, archive_name=self.filepath)
        import_form(import_file=self.filepath)

        updated_form = Form.objects.last()
        registration_backend = updated_form.registration_backends.get()

        self.assertEqual(
            registration_backend.options,
            {
                "variables_mapping": [
                    {
                        "stuf_name": "payment_completed",
                        "form_variable": "payment_completed",
                        "serialize_list_to_csv": False,
                    },
                    {
                        "stuf_name": "payment_amount",
                        "form_variable": "payment_amount",
                        "serialize_list_to_csv": False,
                    },
                    {
                        "stuf_name": "payment_public_order_ids",
                        "form_variable": "payment_public_order_ids",
                        "serialize_list_to_csv": False,
                    },
                    {
                        "stuf_name": "provider_payment_ids",
                        "form_variable": "provider_payment_ids",
                        "serialize_list_to_csv": False,
                    },
                ],
                "zds_zaaktype_code": "test",
                "zds_zaaktype_status_code": "",
                "zds_zaaktype_omschrijving": "",
                "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
                "zds_zaaktype_status_omschrijving": "",
                "zds_documenttype_omschrijving_inzending": "",
            },
        )

    @tag("gh-6254")
    def test_import_with_disable_next_actions(self):
        """
        Assert that the importing legacy forms still works with the disable-next action
        rework.
        """
        # Form, form definitions, and form steps
        form = FormFactory.create(name="Form")
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "checkbox", "label": "Checkbox", "key": "checkbox"}
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "label": "Textfield", "key": "textfield"},
                    {
                        "type": "date",
                        "label": "Date",
                        "key": "date",
                        "prefill": {
                            "plugin": "stufbg",
                            "attribute": "geboortedatum",
                            "identifierRole": "main",
                        },
                    },
                ]
            },
        )
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [{"type": "time", "label": "Time", "key": "time"}]
            },
        )

        # Form variables
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.string,
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined_prefill",
            key="user_defined_prefill",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.date,
            prefill_plugin="stufbg",
            prefill_attribute="geboortedatum",
            prefill_identifier_role="main",
        )

        # Logic rules
        FormLogicFactory.create(
            form=form,
            order=0,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
        )
        FormLogicFactory.create(
            form=form,
            order=1,
            json_logic_trigger={"==": [{"var": "date"}, "2000-01-01"]},
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
        )
        FormLogicFactory.create(
            form=form,
            order=2,
            json_logic_trigger={
                "or": [
                    {"==": [{"var": "textfield"}, "foo"]},
                    {"==": [{"var": "checkbox"}, True]},
                ]
            },
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
            is_advanced=True,
        )
        FormLogicFactory.create(
            form=form,
            order=3,
            json_logic_trigger={"==": [{"var": "user_defined"}, "foo"]},
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
            is_advanced=True,
        )
        FormLogicFactory.create(
            form=form,
            order=4,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "user_defined_prefill"}, "2000-01-01"]},
                    {"==": [{"var": "textfield"}, "foo"]},
                ]
            },
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
            is_advanced=True,
        )
        FormLogic.objects.create(
            form=form,
            order=5,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {"type": "disable-next"},
                    "form_step_uuid": str(step_2.uuid),
                },
            ],
            is_advanced=True,
        )

        export_form(form.pk, archive_name=self.filepath)

        # Import form
        import_form(import_file=self.filepath)

        imported_form = Form.objects.last()
        imported_steps = list(imported_form.formstep_set.all())
        imported_rules = list(imported_form.formlogic_set.all())

        with self.subTest("Single input variable"):
            # Only "checkbox" from the first step is in the trigger
            rule = imported_rules[0]
            self.assertEqual(len(rule.actions), 1)
            self.assertEqual(
                rule.actions[0]["form_step_uuid"], str(imported_steps[0].uuid)
            )

        with self.subTest(
            "First step is added as well if field has prefill configuration"
        ):
            # Components with prefill specified will have a value set upon submission
            # creation, this means executing the rule on the first step has an effect on
            # whether the user can continue. Therefore, even though the input trigger
            # contains "date" from step 2, we need to assign step 1 as well to ensure no
            # changes in behavior.
            rule = imported_rules[1]
            self.assertEqual(len(rule.actions), 2)
            self.assertEqual(
                rule.actions[0]["form_step_uuid"], str(imported_steps[0].uuid)
            )
            self.assertEqual(
                rule.actions[1]["form_step_uuid"], str(imported_steps[1].uuid)
            )
            self.assertEqual(rule.actions[1]["action"], {"type": "disable-next"})

        with self.subTest("Logic trigger contains input variables from multiple steps"):
            # The logic trigger contains fields from steps 1 and 2, so ensure we add a
            # disable-next action for both
            rule = imported_rules[2]
            self.assertEqual(len(rule.actions), 2)
            self.assertEqual(
                rule.actions[0]["form_step_uuid"], str(imported_steps[0].uuid)
            )
            self.assertEqual(
                rule.actions[1]["form_step_uuid"], str(imported_steps[1].uuid)
            )
            self.assertEqual(rule.actions[1]["action"], {"type": "disable-next"})

        with self.subTest("With user-defined variable"):
            # The logic trigger only contains a user-defined variable, and the rule does
            # not have the "trigger_from_step" defined, so we cannot resolve a step.
            # Ensure we assign the first step as a best guess.
            rule = imported_rules[3]
            self.assertEqual(len(rule.actions), 1)
            self.assertEqual(
                rule.actions[0]["form_step_uuid"], str(imported_steps[0].uuid)
            )

        with self.subTest(
            "First step is added as well when user-defined variable has prefill "
            "configuration"
        ):
            # The trigger contains "textfield" from the second step, and a user-defined
            # variable with prefill. Ensure that we add the first and second step in
            # this case, because prefilled data are available upon submission creation.
            rule = imported_rules[4]
            self.assertEqual(len(rule.actions), 2)
            self.assertEqual(
                rule.actions[0]["form_step_uuid"], str(imported_steps[0].uuid)
            )
            self.assertEqual(
                rule.actions[1]["form_step_uuid"], str(imported_steps[1].uuid)
            )
            self.assertEqual(rule.actions[1]["action"], {"type": "disable-next"})

        with self.subTest("Already configured disable-next action is left alone"):
            # According to our analysis, the first step should be assigned to this
            # action, but the second was already configured, so we leave it be.
            rule = imported_rules[5]
            self.assertEqual(len(rule.actions), 1)
            self.assertEqual(
                rule.actions[0]["form_step_uuid"], str(imported_steps[1].uuid)
            )


class ExportObjectsAPITests(TempdirMixin, TestCase):
    @tag("gh-5384")
    def test_export_form_with_objects_registration_backend(self):
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            identifier="test-objects-api-group"
        )
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            backend="objects_api",
            key="test-objects-backend",
            options={
                "objects_api_group": objects_api_group.identifier,
            },
        )

        export_form(form.pk, archive_name=self.filepath)

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
            self.assertEqual(len(forms[0]["registration_backends"]), 1)
            self.assertEqual(
                forms[0]["registration_backends"][0]["key"], "test-objects-backend"
            )
            self.assertEqual(
                forms[0]["registration_backends"][0]["options"]["objects_api_group"],
                "test-objects-api-group",
            )


class ImportObjectsAPITests(TempdirMixin, OFVCRMixin, TestCase):
    """This test case requires the Objects & Objecttypes API and Open Zaak to be running.

    See the relevant Docker compose in the ``docker/`` folder.
    """

    def test_import_form_with_objects_registration_backend_no_group(self):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "objects-api-no-group",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        with self.assertRaises(ValidationError) as exc:
            import_form(import_file=self.filepath)

        error_detail = exc.exception.detail["registration_backends"][0]["options"][
            "objects_api_group"
        ][0]
        self.assertEqual(error_detail.code, "required")

    def test_import_form_with_objecttype_url_objects_api_registration_backend(self):
        """Test forms with an Objects API registration backend where objecttype is specified as an URL
        doesn't gets converted to a UUID and throws an Error.
        """

        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "old-objecttype-url",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": ObjectsAPIGroupConfigFactory.create(
                                    for_test_docker_compose=True
                                ).identifier,
                                "version": 2,
                                "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        with self.assertRaises(ValidationError) as exc:
            import_form(import_file=self.filepath)

        error_detail = exc.exception.detail["registration_backends"][0]["options"][
            "objecttype"
        ][0]
        self.assertEqual(error_detail, "Must be a valid UUID.")
        self.assertEqual(error_detail.code, "invalid")

        with self.assertRaises(FormRegistrationBackend.DoesNotExist):
            FormRegistrationBackend.objects.get(key="test-backend")

    def test_import_form_with_objecttype_uuid_objects_api_registration_backend(self):
        """Test forms with an Objects API registration backend where objecttype is specified as an UUID
        stays as is.
        """

        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "old-objecttype-url",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": ObjectsAPIGroupConfigFactory.create(
                                    for_test_docker_compose=True
                                ).identifier,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        registration_backend = FormRegistrationBackend.objects.get(key="test-backend")
        self.assertEqual(
            registration_backend.options["objecttype"],
            "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
        )

    def test_import_form_with_objects_registration_backend_no_version_and_no_variables_mapping(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "objects-api-no-group",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": ObjectsAPIGroupConfigFactory.create(
                                    for_test_docker_compose=True
                                ).identifier,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        registration_backend = FormRegistrationBackend.objects.get(key="test-backend")

        # By default, a new Objects API registration is set to version 2.
        # If a v2 Objects API registrations doesn't provide a `variables_mapping` it's
        # set to empty array.
        self.assertEqual(registration_backend.options["version"], 2)
        self.assertEqual(registration_backend.options["variables_mapping"], [])

    def test_import_form_with_objects_registration_backend_without_variables_mapping(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "objects-api-no-group",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend-v1",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": ObjectsAPIGroupConfigFactory.create(
                                    for_test_docker_compose=True
                                ).identifier,
                                "version": 1,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        },
                        {
                            "key": "test-backend-v2",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": ObjectsAPIGroupConfigFactory.create(
                                    for_test_docker_compose=True
                                ).identifier,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                            },
                        },
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        registration_backend_v1 = FormRegistrationBackend.objects.get(
            key="test-backend-v1"
        )
        registration_backend_v2 = FormRegistrationBackend.objects.get(
            key="test-backend-v2"
        )

        # Only when a Objects API registration is v2, has the `variables_mapping` a
        # default value.
        self.assertEqual(registration_backend_v1.options["version"], 1)
        self.assertNotIn("variables_mapping", registration_backend_v1.options)

        self.assertEqual(registration_backend_v2.options["version"], 2)
        self.assertIn("variables_mapping", registration_backend_v2.options)
        self.assertEqual(registration_backend_v2.options["variables_mapping"], [])

    def test_import_form_with_objects_registration_backend_with_valid_variables_mapping(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "objects-api-no-group",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": ObjectsAPIGroupConfigFactory.create(
                                    for_test_docker_compose=True
                                ).identifier,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                                "variables_mapping": [
                                    {"variable_key": "data", "options": {}}
                                ],
                            },
                        },
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        registration_backend_valid_mapping = FormRegistrationBackend.objects.get(
            key="test-backend"
        )

        # The valid variables_mapping is left as is
        self.assertIn("variables_mapping", registration_backend_valid_mapping.options)
        self.assertEqual(
            registration_backend_valid_mapping.options["variables_mapping"],
            [{"variable_key": "data", "options": {}}],
        )

    def test_import_form_with_objects_registration_backend_with_invalid_variables_mapping(
        self,
    ):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "objects-api-no-group",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": ObjectsAPIGroupConfigFactory.create(
                                    for_test_docker_compose=True
                                ).identifier,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 1,
                                "variables_mapping": {},
                            },
                        },
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        with self.assertRaises(ValidationError) as exc:
            import_form(import_file=self.filepath)

        error_detail = exc.exception.detail["registration_backends"][0]["options"][
            "variables_mapping"
        ]["non_field_errors"][0]
        self.assertEqual(error_detail.code, "not_a_list")

    @tag("gh-5384")
    def test_import_form_with_objects_api_group_pk(self):
        """
        test that there is a backward compatibility after objects_api_group attribute
        was converted from pk to slug
        """
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "test-form-1",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": [
                        {
                            "key": "test-backend",
                            "name": "Test backend",
                            "backend": "objects_api",
                            "options": {
                                "objects_api_group": objects_api_group.pk,
                                "version": 2,
                                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                                "objecttype_version": 2,
                            },
                        }
                    ],
                }
            ]
        }

        with zipfile.ZipFile(self.filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

        import_form(import_file=self.filepath)

        registration_backend = FormRegistrationBackend.objects.get(key="test-backend")
        self.assertEqual(
            registration_backend.options["objects_api_group"],
            objects_api_group.identifier,
        )

    def test_import_form_with_legacy_file_registration_options(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "toplevel.file1",
                        "label": "Top level file",
                        "file": {"type": []},
                        "filePattern": "",
                        "registration": {
                            "bronorganisatie": "100000009",
                            "docVertrouwelijkheidaanduiding": "geheim",
                            "titel": "Custom title",
                            "documentType": {
                                "catalogue": {
                                    "domain": "TEST",
                                    "rsin": "000000000",
                                },
                                "description": "PDF Informatieobjecttype",
                            },
                        },
                    },
                    {
                        "type": "file",
                        "key": "toplevel.file2",
                        "label": "Top level file 2",
                        "file": {"type": []},
                        "filePattern": "",
                    },
                    {
                        "type": "file",
                        "key": "toplevel.file3",
                        "label": "Top level file 3",
                        "file": {"type": []},
                        "filePattern": "",
                        "registration": {"titel": ""},
                    },
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Repeating group",
                        "groupLabel": "Item",
                        "components": [
                            {
                                "type": "file",
                                "key": "editgridFile",
                                "label": "Editgrid file",
                                "file": {"type": []},
                                "filePattern": "",
                                "registration": {
                                    "bronorganisatie": "100000009",
                                    "titel": "Another title",
                                },
                            }
                        ],
                    },
                ]
            },
        )
        group = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)
        options: ObjectsRegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": group,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "Attachment Informatieobjecttype",
            "variables_mapping": [],
            "transform_to_list": [],
        }
        FormRegistrationBackend.objects.create(
            form=form,
            name="Objects 1",
            key="objects1",
            backend=OBJECTS_API_PLUGIN_IDENTIFIER,
            options=ObjectsAPIOptionsSerializer(instance=options).data,
        )
        FormRegistrationBackend.objects.create(
            form=form,
            name="Objects 2",
            key="objects2",
            backend=OBJECTS_API_PLUGIN_IDENTIFIER,
            options={
                **ObjectsAPIOptionsSerializer(instance=options).data,
                "files": [],
            },
        )
        export_form(form.pk, archive_name=self.filepath)
        form.delete()

        import_form(import_file=self.filepath)

        backends: dict[str, FormRegistrationBackend] = {
            backend.key: backend for backend in FormRegistrationBackend.objects.all()
        }
        with self.subTest("backend without file options gets them added"):
            backend_without_initial_files = backends["objects1"]
            assert "files" in backend_without_initial_files.options
            file_options = {
                opts["key"]: opts
                for opts in backend_without_initial_files.options["files"]
            }
            self.assertEqual(
                file_options,
                {
                    "toplevel.file1": {
                        "key": "toplevel.file1",
                        "document_type_description": "PDF Informatieobjecttype",
                        "organization_rsin": "100000009",
                        "confidentiality_level": "geheim",
                        "title": "Custom title",
                    },
                    "editgridFile": {
                        "key": "editgridFile",
                        "organization_rsin": "100000009",
                        "title": "Another title",
                    },
                },
            )

        with self.subTest("backend with file options is untouched"):
            backend_with_initial_files = backends["objects2"]
            assert "files" in backend_with_initial_files.options
            self.assertEqual(len(backend_with_initial_files.options["files"]), 0)


class ImportZGWAPITests(TempdirMixin, OFVCRMixin, TestCase):
    """This test case requires the Open Zaak Docker Compose to be running.

    See the relevant Docker compose in the ``docker/`` folder.
    """

    @staticmethod
    def _create_export(filepath: Path, *backends: dict):
        resources = {
            "forms": [
                {
                    "active": True,
                    "name": "Test Form 1",
                    "internal_name": "Test Form Internal 1",
                    "slug": "zgw-group",
                    "uuid": "324cadce-a627-4e3f-b117-37ca232f16b2",
                    "registration_backends": list(backends),
                }
            ]
        }

        with zipfile.ZipFile(filepath, "w") as zip_file:
            for name, data in resources.items():
                zip_file.writestr(f"{name}.json", json.dumps(data))

    def test_import_form_with_zgw_registration_backend_with_objects_api_group_apply_default(
        self,
    ):
        """
        In legacy imports, `options.objects_api_group` was not required, because the plugin
        always used the ObjectsAPIGroup with the lowest primary key at runtime. Because
        `options.objects_api_group` has now been made required, this should be injected
        into the import data to make sure the import still works
        """
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        api_group = ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)
        self._create_export(
            self.filepath,
            {
                "key": "test-backend",
                "name": "Test backend",
                "backend": "zgw-create-zaak",
                "options": {
                    "zgw_api_group": api_group.pk,
                    "catalogue": {"domain": "", "rsin": ""},
                    "zaaktype": "http://localhost:8003/catalogi/api/v1/zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
                    "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
                    "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                    "objecttype_version": 1,
                },
            },
        )

        import_form(import_file=self.filepath)

        registration_backend = FormRegistrationBackend.objects.get(key="test-backend")
        self.assertEqual(
            registration_backend.options["objects_api_group"],
            objects_api_group.identifier,
        )

    def test_import_form_with_zgw_registration_backend_cant_determine_objects_api_group(
        self,
    ):
        zgw_group = ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)

        with self.subTest("no default group exists"):
            self._create_export(
                self.filepath,
                {
                    "key": "test-backend",
                    "name": "Test backend",
                    "backend": "zgw-create-zaak",
                    "options": {
                        "zgw_api_group": zgw_group.pk,
                        "catalogue": {"domain": "", "rsin": ""},
                        "zaaktype": "http://localhost:8003/catalogi/api/v1/zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
                        "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
                        "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                    },
                },
            )

            with self.assertRaises(ValidationError) as exc:
                import_form(import_file=self.filepath)

            error_detail = exc.exception.detail["registration_backends"][0]["options"][
                "objects_api_group"
            ][0]
            self.assertEqual(error_detail.code, "required")

        with self.subTest("objects API group present in export"):
            objects_api_group = ObjectsAPIGroupConfigFactory.create(
                for_test_docker_compose=True
            )
            self._create_export(
                self.filepath,
                {
                    "key": "test-backend",
                    "name": "Test backend",
                    "backend": "zgw-create-zaak",
                    "options": {
                        "zgw_api_group": zgw_group.pk,
                        "catalogue": {"domain": "", "rsin": ""},
                        "zaaktype": "http://localhost:8003/catalogi/api/v1/zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc",
                        "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
                        "objects_api_group": objects_api_group.identifier,
                        "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                    },
                },
            )

            import_form(import_file=self.filepath)

            registration_backend = FormRegistrationBackend.objects.get(
                key="test-backend"
            )
            self.assertEqual(
                registration_backend.options["objects_api_group"],
                objects_api_group.identifier,
            )


class DisableNextImportConversionTests(TestCase):
    def test_with_trigger_from_step(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "checkbox", "label": "Checkbox", "key": "checkbox"}
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "label": "Textfield", "key": "textfield"},
                ]
            },
        )
        step_3 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "time", "label": "Time", "key": "time"},
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            order=4,
            json_logic_trigger={
                "or": [
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "textfield"}, "foo"]},
                    {"==": [{"var": "time"}, "12:34"]},
                ]
            },
            actions=[{"action": {"type": "disable-next"}, "form_step_uuid": ""}],
            trigger_from_step=step_2,
            is_advanced=True,
        )

        # Resembles an exported rule
        rule = {
            "uuid": "62f75ecb-a860-464e-a1d9-0a6debc4ddd8",
            "url": f"http://testserver/api/v2/forms/{form.uuid}/logic-rules",
            "form": f"http://testserver/api/v2/forms/{form.uuid}",
            "json_logic_trigger": {
                "or": [
                    {"==": [{"var": "checkbox"}, True]},
                    {"==": [{"var": "textfield"}, "foo"]},
                    {"==": [{"var": "time"}, "12:34"]},
                ]
            },
            "description": "",
            "order": 0,
            "trigger_from_step": f"http://testserver/api/v2/forms/{form.uuid}/steps/{step_2.uuid}",
            "actions": [
                {
                    "component": "",
                    "form_step_uuid": "",
                    "action": {"type": "disable-next"},
                }
            ],
            "is_advanced": True,
            "form_steps": [],
        }

        add_form_step_uuid_to_disable_next_actions(
            rule,
            {var.key: var for var in form.formvariable_set.all()},
            {step.uuid: step for step in form.formstep_set.all()},
        )

        # The trigger also contains "checkbox" from step 1, but it shouldn't be
        # included in the actions because the "trigger_from_step" is set to step 2.
        self.assertEqual(len(rule["actions"]), 2)
        self.assertEqual(rule["actions"][0]["form_step_uuid"], str(step_2.uuid))
        self.assertEqual(rule["actions"][1]["form_step_uuid"], str(step_3.uuid))
        self.assertEqual(rule["actions"][1]["action"], {"type": "disable-next"})
