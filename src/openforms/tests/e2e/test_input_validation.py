"""
Test that the input validation performed on the backend matches the one on the frontend.

The frontend/formio validation implementation is leading here.

Note that the actual test input/output is defined in the YAML-files in the
input_validation subdirectory.
"""

from pathlib import Path
from typing import Any

from django.core.files import File
from django.urls import reverse

from asgiref.sync import async_to_sync
from furl import furl
from playwright.async_api import Page, expect

from openforms.formio.constants import DataSrcOptions
from openforms.formio.tests.factories import SubmittedFileFactory
from openforms.formio.typing import (
    AddressNLComponent,
    Component,
    DateComponent,
    DatetimeComponent,
    RadioComponent,
)
from openforms.forms.models import Form
from openforms.submissions.models import TemporaryFileUpload
from openforms.submissions.tests.factories import TemporaryFileUploadFactory

from .base import browser_page
from .input_validation_base import ValidationsTestCase, create_form

TEST_CASES = (Path(__file__).parent / "input_validation").resolve()
TEST_FILES = Path(__file__).parent / "data"


class SingleTextFieldTests(ValidationsTestCase):

    def test_required_field(self):
        component: Component = {
            "type": "textfield",
            "key": "requiredTextField",
            "label": "Required text field",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required text field is niet ingevuld.",
        )

    def test_max_length(self):
        component: Component = {
            "type": "textfield",
            "key": "maxLengthTextField",
            "label": "Max length 3",
            "validate": {"maxLength": 3},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="too long",
            expected_ui_error="Er zijn teveel karakters opgegeven.",
        )

    def test_regex_huisletter(self):
        component: Component = {
            "type": "textfield",
            "key": "houseLetter",
            "label": "Huisletter",
            "validate": {"pattern": "[a-zA-Z]"},
            "errors": {"pattern": "Huisletter moet een letter zijn."},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="<h2>test</h2>",
            expected_ui_error="Huisletter moet een letter zijn.",
        )

    def test_regex_house_number_addition(self):
        component: Component = {
            "type": "textfield",
            "key": "houseNumberAddition",
            "label": "Toevoeging huisnummer",
            "validate": {"pattern": "[a-zA-Z0-9]{1,4}"},
            "errors": {
                "pattern": "Huisnummertoevoeging mag enkel alfanumerieke karaketers zijn."
            },
        }

        self.assertValidationIsAligned(
            component,
            ui_input="<h1>test</h1>",
            expected_ui_error="Huisnummertoevoeging mag enkel alfanumerieke karaketers zijn.",
        )

    def test_kvk_number_validation_plugin(self):
        component: Component = {
            "type": "textfield",
            "key": "chamberOfCommerce",
            "label": "KVK nummer",
            "validate": {
                "plugins": ["kvk-kvkNumber"],
            },
        }

        self.assertValidationIsAligned(
            component,
            ui_input="aaaa",  # deliberate to trigger the non-network validation
            expected_ui_error="Waarde moet numeriek zijn.",
        )


class SingleEmailTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "email",
            "key": "requiredEmail",
            "label": "Required email",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required email is niet ingevuld.",
        )

    def test_email_format(self):
        component: Component = {
            "type": "email",
            "key": "email",
            "label": "E-mailadres",
        }

        self.assertValidationIsAligned(
            component,
            ui_input="invalid",
            expected_ui_error="Ongeldig e-mailadres",
        )


class SingleNumberTests(ValidationsTestCase):

    def test_required_field(self):
        component: Component = {
            "type": "number",
            "key": "requiredNumber",
            "label": "Required number",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            api_value=None,
            expected_ui_error="Het verplichte veld Required number is niet ingevuld.",
        )

    def test_min_value(self):
        component: Component = {
            "type": "number",
            "key": "minValue",
            "label": "Minimum value",
            "validate": {"min": 3},
        }

        self.assertValidationIsAligned(
            component,
            ui_input=2,
            expected_ui_error="De waarde moet 3 of groter zijn.",
        )

    def test_max_value(self):
        component: Component = {
            "type": "number",
            "key": "maxValue",
            "label": "Maximum value",
            "validate": {"max": 42},
        }

        self.assertValidationIsAligned(
            component,
            ui_input=50,
            expected_ui_error="De waarde moet 42 of kleiner zijn.",
        )


class RadioTests(ValidationsTestCase):
    async def apply_ui_input(self, page: Page, label: str, ui_input: str | int | float):
        """
        Check the radio input labeled by ``ui_input``.
        """
        assert isinstance(ui_input, str)

        # no option to select -> do nothing
        if not ui_input:
            return

        await page.get_by_label(ui_input).click()

    def test_required_field(self):
        component: RadioComponent = {
            "type": "radio",
            "key": "requiredRadio",
            "label": "Required radio",
            "validate": {"required": True},
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
            ],
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required radio is niet ingevuld.",
        )


class SingleBSNTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "bsn",
            "key": "requiredBSN",
            "label": "Required bsn",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required bsn is niet ingevuld.",
        )

    def test_elfproef_invalid_num_chars(self):
        component: Component = {
            "type": "bsn",
            "key": "bsnTooShort",
            "label": "BSN too short",
        }

        self.assertValidationIsAligned(
            component,
            ui_input="1234",
            expected_ui_error="Ongeldig BSN",
        )

    def test_elfproef_invalid_bsn(self):
        component: Component = {
            "type": "bsn",
            "key": "invalidBSN",
            "label": "Invalid bsn",
        }
        self.assertValidationIsAligned(
            component,
            ui_input="123456781",
            expected_ui_error="Ongeldig BSN",
        )


class SingleDateTests(ValidationsTestCase):

    async def apply_ui_input(
        self, page: Page, label: str, ui_input: str | int | float = ""
    ) -> None:
        assert isinstance(ui_input, str)
        # fix the input resolution because the formio datepicker is not accessible
        label_node = page.get_by_text(label, exact=True)
        label_parent = label_node.locator("xpath=../..")
        input_node = label_parent.get_by_role("textbox", include_hidden=False)
        await input_node.fill(ui_input)

    def test_required_field(self):
        component: DateComponent = {
            "type": "date",
            "key": "requiredDate",
            "label": "Required date field",
            "validate": {"required": True},
            "datePicker": {
                "showWeeks": True,
                "startingDay": 0,
                "initDate": "",
                "minMode": "day",
                "maxMode": "year",
                "yearRows": 4,
                "yearColumns": 5,
                "minDate": None,
                "maxDate": None,
            },
            "customOptions": {"allowInvalidPreload": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required date field is niet ingevuld.",
        )

    def test_min_date_fixed_value(self):
        component: DateComponent = {
            "type": "date",
            "key": "minDate",
            "label": "Minimum date",
            "openForms": {
                "minDate": {"mode": "fixedValue"},
            },
            "datePicker": {
                "showWeeks": True,
                "startingDay": 0,
                "initDate": "",
                "minMode": "day",
                "maxMode": "year",
                "yearRows": 4,
                "yearColumns": 5,
                "minDate": "2024-03-13",
                "maxDate": None,
            },
            "customOptions": {"allowInvalidPreload": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="01-01-2024",
            api_value="2024-01-01",
            expected_ui_error="De opgegeven datum ligt te ver in het verleden.",
        )

    def test_max_date_fixed_value(self):
        component: DateComponent = {
            "type": "date",
            "key": "maxDate",
            "label": "Maximum date",
            "openForms": {
                "maxDate": {"mode": "fixedValue"},
            },
            "datePicker": {
                "showWeeks": True,
                "startingDay": 0,
                "initDate": "",
                "minMode": "day",
                "maxMode": "year",
                "yearRows": 4,
                "yearColumns": 5,
                "maxDate": "2024-03-13",
                "minDate": None,
            },
            "customOptions": {"allowInvalidPreload": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="01-01-2025",
            api_value="2025-01-01",
            expected_ui_error="De opgegeven datum ligt te ver in de toekomst.",
        )


class SingleDatetimeTests(ValidationsTestCase):
    # Component configuration set via js/components/form/datetime.js
    JS_CONFIG = {
        "format": "dd-MM-yyyy HH:mm",
        "placeholder": "dd-MM-yyyy HH:mm",
        "enableTime": True,
        "time_24hr": True,
        "timePicker": {
            "hourStep": 1,
            "minuteStep": 1,
            "showMeridian": False,
            "readonlyInput": False,
            "mousewheel": True,
            "arrowkeys": True,
        },
    }

    async def apply_ui_input(
        self, page: Page, label: str, ui_input: str | int | float = ""
    ) -> None:
        assert isinstance(ui_input, str)
        # fix the input resolution because the formio datepicker is not accessible
        label_node = page.get_by_text(label, exact=True)
        label_parent = label_node.locator("xpath=../..")
        input_node = label_parent.get_by_role("textbox", include_hidden=False)
        await input_node.fill(ui_input)

    def test_required_field(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "requiredDatetime",
            "label": "Required datetime field",
            **self.JS_CONFIG,
            "validate": {"required": True},
            "datePicker": {
                "showWeeks": True,
                "startingDay": 0,
                "initDate": "",
                "minMode": "day",
                "maxMode": "year",
                "yearRows": 4,
                "yearColumns": 5,
                "minDate": None,
                "maxDate": None,
            },
            "customOptions": {"allowInvalidPreload": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required datetime field is niet ingevuld.",
        )

    def test_min_date_fixed_value(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "minDatetime",
            "label": "Minimum date",
            **self.JS_CONFIG,
            "openForms": {
                "minDate": {"mode": "fixedValue"},
            },
            "datePicker": {
                "showWeeks": True,
                "startingDay": 0,
                "initDate": "",
                "minMode": "day",
                "maxMode": "year",
                "yearRows": 4,
                "yearColumns": 5,
                "minDate": "2024-03-13T11:00",  # Europe/Amsterdam timezone?
                "maxDate": None,
            },
            "customOptions": {"allowInvalidPreload": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="13-03-2024 10:59",
            api_value="2024-03-13T10:59:00+01:00",
            expected_ui_error="De opgegeven datum ligt te ver in het verleden.",
        )

    def test_max_date_fixed_value(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "maxDatetime",
            "label": "Maximum date",
            **self.JS_CONFIG,
            "openForms": {
                "maxDate": {"mode": "fixedValue"},
            },
            "datePicker": {
                "showWeeks": True,
                "startingDay": 0,
                "initDate": "",
                "minMode": "day",
                "maxMode": "year",
                "yearRows": 4,
                "yearColumns": 5,
                "maxDate": "2024-03-13T12:00:00+00:00",
                "minDate": None,
            },
            "customOptions": {"allowInvalidPreload": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="13-03-2024 13:01",
            api_value="2024-03-13T13:01:00+01:00",
            expected_ui_error="De opgegeven datum ligt te ver in de toekomst.",
        )


class SingleCheckboxTests(ValidationsTestCase):

    async def apply_ui_input(self, page: Page, label: str, ui_input: str | int | float):
        await expect(page.get_by_role("checkbox", name=label)).not_to_be_checked()

    def test_required_field(self):
        component: Component = {
            "type": "checkbox",
            "key": "requiredCheckbox",
            "label": "Required checkbox",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            api_value=False,
            expected_ui_error="Het verplichte veld Required checkbox is niet ingevuld.",
        )


class SingleCurrencyTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "currency",
            "key": "requiredCurrency",
            "label": "Required currency",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required currency is niet ingevuld.",
        )

    def test_min_value(self):
        component: Component = {
            "type": "currency",
            "key": "minValueCurrency",
            "label": "Min value currency",
            "validate": {"min": 10.7},
        }

        self.assertValidationIsAligned(
            component,
            ui_input=2,
            expected_ui_error="De waarde moet 10.7 of groter zijn.",
        )

    def test_max_value(self):
        component: Component = {
            "type": "currency",
            "key": "maxValueCurrency",
            "label": "Max value currency",
            "validate": {"max": 15},
        }

        self.assertValidationIsAligned(
            component,
            ui_input=50,
            expected_ui_error="De waarde moet 15 of kleiner zijn.",
        )


class SingleMapTests(ValidationsTestCase):
    fuzzy_match_invalid_param_names = True

    async def apply_ui_input(self, page: Page, label: str, ui_input: str | int | float):
        await page.wait_for_selector(
            f".openforms-leaflet-map, [aria-label='{label}']", state="visible"
        )

    def test_required_field(self):
        component: Component = {
            "type": "map",
            "key": "requiredMap",
            "label": "Required map",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required map is niet ingevuld.",
        )


class SinglePostcodeTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "postcode",
            "key": "requiredPostcode",
            "label": "Required postcode",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required postcode is niet ingevuld.",
        )


class SingleSignatureTests(ValidationsTestCase):

    async def apply_ui_input(self, page: Page, label: str, ui_input: str | int | float):
        # can't do anything because it's a canvas, but we can assert that the label
        # is rendered.
        await expect(page.get_by_text(label, exact=True)).to_be_visible()

    def test_required_field(self):
        component: Component = {
            "type": "signature",
            "key": "requiredSignature",
            "label": "Required signature",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required signature is niet ingevuld.",
        )


class SingleTextAreaTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "textarea",
            "key": "requiredTextarea",
            "label": "Required textarea",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required textarea is niet ingevuld.",
        )

    def test_max_length(self):
        component: Component = {
            "type": "textarea",
            "key": "maxLengthTextarea",
            "label": "Max length textarea",
            "validate": {"maxLength": 10},
        }
        invalid_sample = "word" * 4

        self.assertValidationIsAligned(
            component,
            ui_input=invalid_sample,
            expected_ui_error="Er zijn teveel karakters opgegeven.",
        )


class SingleTimeTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "time",
            "key": "requiredTime",
            "label": "Required time",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required time is niet ingevuld.",
        )

    def test_min_value(self):
        component: Component = {
            "type": "time",
            "key": "minTime",
            "label": "Minimum time",
            "validate": {
                "minTime": "10:00",
                "maxTime": "12:00",
            },
        }

        self.assertValidationIsAligned(
            component,
            ui_input="09:10",
            expected_ui_error="Alleen tijden tussen 10:00 en 12:00 zijn toegestaan.",
        )

    def test_max_value(self):
        component: Component = {
            "type": "time",
            "key": "maxTime",
            "label": "Maximum time",
            "validate": {
                "minTime": "10:00",
                "maxTime": "12:00",
            },
        }

        self.assertValidationIsAligned(
            component,
            ui_input="12:10",
            expected_ui_error="Alleen tijden tussen 10:00 en 12:00 zijn toegestaan.",
        )

    def test_min_max_crossing_midnight(self):
        component: Component = {
            "type": "time",
            "key": "nextDayTime",
            "label": "Next day min/max time",
            "validate": {
                "minTime": "20:00",
                "maxTime": "04:00",
            },
        }

        self.assertValidationIsAligned(
            component,
            ui_input="15:00",
            expected_ui_error="Alleen tijden tussen 20:00 en 04:00 zijn toegestaan.",
        )


class SingleCosignTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "cosign",
            "key": "requiredCosign",
            "label": "Required cosign",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required cosign is niet ingevuld.",
        )

    def test_cosign_format(self):
        component: Component = {
            "type": "cosign",
            "key": "cosign",
            "label": "Cosign",
        }

        self.assertValidationIsAligned(
            component,
            ui_input="invalid",
            expected_ui_error="Ongeldig e-mailadres",
        )


class SingleIbanTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "iban",
            "key": "requiredIban",
            "label": "Required iban",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required iban is niet ingevuld.",
        )

    def test_invalid_field(self):
        component: Component = {
            "type": "iban",
            "key": "requiredIban",
            "label": "Required iban",
        }

        self.assertValidationIsAligned(
            component,
            ui_input="NL12 3456 789I I987 6999",
            expected_ui_error="Ongeldig IBAN",
        )


class SingleLicenseplateTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "licenseplate",
            "key": "requiredLicenseplate",
            "label": "Required licenseplate",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required licenseplate is niet ingevuld.",
        )

    def test_regex_pattern(self):
        component: Component = {
            "type": "licenseplate",
            "key": "regexPatternLicenseplate",
            "label": "Regex pattern licenseplate",
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}$"
            },
            "errors": {"pattern": "Ongeldig Nederlands kenteken"},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="<h2>test</h2>",
            expected_ui_error="Ongeldig Nederlands kenteken",
        )


class SingleFileTests(ValidationsTestCase):
    fuzzy_match_invalid_param_names = True

    def assertFileValidationIsAligned(
        self,
        component: Component,
        ui_files: list[Path],
        expected_ui_error: str,
        api_value: list[dict[str, Any]],
    ) -> None:
        form = create_form(component)

        with self.subTest("frontend validation"):
            self._assertFileFrontendValidation(form, ui_files, expected_ui_error)

        with self.subTest("backend validation"):
            self._assertBackendValidation(form, component["key"], api_value)

    @async_to_sync
    async def _assertFileFrontendValidation(
        self, form: Form, ui_files: list[Path], expected_ui_error: str
    ) -> None:
        frontend_path = reverse("forms:form-detail", kwargs={"slug": form.slug})
        url = str(furl(self.live_server_url) / frontend_path)

        async with browser_page() as page:
            await page.goto(url)
            await page.get_by_role("button", name="Formulier starten").click()

            async with page.expect_file_chooser() as fc_info:
                await page.get_by_text("blader").click()

            file_chooser = await fc_info.value
            await file_chooser.set_files(ui_files)
            await page.wait_for_load_state("networkidle")

            # try to submit the step which should be invalid, so we expect this to
            # render the error message.
            await page.get_by_role("button", name="Volgende").click()
            await expect(page.get_by_text(expected_ui_error)).to_be_visible()

    def test_required_field(self):
        component = {
            "type": "file",
            "key": "requiredFile",
            "label": "Required file",
            "validate": {"required": True},
            "storage": "url",
        }

        self.assertFileValidationIsAligned(
            component,
            ui_files=[],
            expected_ui_error="Het verplichte veld Required file is niet ingevuld.",
            api_value=[],
        )

    def test_bad_pdf(self):
        component = {
            "type": "file",
            "key": "badPdf",
            "label": "Bad PDF",
            "validate": {"required": True},
            "storage": "url",
        }

        # The frontend validation will *not* create a TemporaryFileUpload,
        # as the endpoint will return a 400 because of the bad content type.
        # For this reason, we use a random UUID for the `api_value`

        self.assertFileValidationIsAligned(
            component,
            ui_files=[TEST_FILES / "image-256x256.pdf"],
            expected_ui_error="Het bestand is geen .pdf.",
            api_value=[
                SubmittedFileFactory.build(
                    type="application/pdf",
                    url="http://localhost/api/v2/submissions/files/d4c97feb-68f6-4b85-9b78-7a74ee48b072",
                    data__url="http://localhost/api/v2/submissions/files/d4c97feb-68f6-4b85-9b78-7a74ee48b072",
                )
            ],
        )

        # Make sure the frontend did not create one:
        self.assertFalse(TemporaryFileUpload.objects.exists())

    def test_forbidden_file_type(self):
        component = {
            "type": "file",
            "key": "badPdf",
            "label": "Bad PDF",
            "validate": {"required": True},
            "storage": "url",
            "file": {
                "type": [
                    "application/pdf",
                ],
                "allowedTypesLabels": [
                    ".pdf",
                ],
            },
            "filePattern": "application/pdf",
        }

        # The frontend validation will *not* create a TemporaryFileUpload,
        # as the frontend will block the upload because of the invalid file type.
        # However the user could do an handcrafted API call.
        # For this reason, we manually create an invalid TemporaryFileUpload
        # and use it for the `api_value`:
        with open(TEST_FILES / "image-256x256.png", "rb") as infile:
            temporary_upload = TemporaryFileUploadFactory.create(
                file_name="image-256x256.png",
                content=File(infile),
                content_type="image/png",
            )

        self.assertFileValidationIsAligned(
            component,
            ui_files=[TEST_FILES / "image-256x256.png"],
            expected_ui_error="Het geuploaded bestand is niet van een toegestaan type. Het moet .pdf zijn.",
            api_value=[
                SubmittedFileFactory.create(
                    temporary_upload=temporary_upload,
                    type="image/png",
                )
            ],
        )

        # Make sure the frontend did not create one:
        self.assertEqual(TemporaryFileUpload.objects.count(), 1)

    def test_unknown_file_type(self):
        component = {
            "type": "file",
            "key": "unknownFile",
            "label": "Unknown File",
            "validate": {"required": True},
            "storage": "url",
            "file": {
                "type": [
                    "",
                ],
                "allowedTypesLabels": [
                    "*",
                ],
            },
        }

        # The frontend validation will *not* create a TemporaryFileUpload,
        # as the frontend will block the upload because of the invalid file type.
        # However the user could do a handcrafted API call.
        # For this reason, we manually try to create an invalid TemporaryFileUpload
        # and use it for the `api_value`:

        with open(TEST_FILES / "unknown-type", "rb") as infile:
            temporary_upload = TemporaryFileUploadFactory.build(
                file_name="unknown-type-file",
                content=File(infile),
                content_type="",
            )

            self.assertFileValidationIsAligned(
                component,
                ui_files=[TEST_FILES / "unknown-type"],
                expected_ui_error=(
                    "Het bestandstype kon niet bepaald worden. Controleer of de "
                    "bestandsnaam met een extensie eindigt (bijvoorbeeld '.pdf' of "
                    "'.png')."
                ),
                api_value=[
                    SubmittedFileFactory.create(
                        temporary_upload=temporary_upload,
                        type="",
                    )
                ],
            )

        # Make sure that no temporary files were created
        self.assertEqual(TemporaryFileUpload.objects.count(), 0)


class SingleAddressNLTests(ValidationsTestCase):
    fuzzy_match_invalid_param_names = True

    def assertAddressNLValidationIsAligned(
        self,
        component: AddressNLComponent,
        ui_inputs: dict[str, str],
        expected_ui_error: str,
        api_value: dict[str, Any],
    ) -> None:
        form = create_form(component)

        with self.subTest("frontend validation"):
            self._assertAddressNLFrontendValidation(form, ui_inputs, expected_ui_error)

        with self.subTest("backend validation"):
            self._assertBackendValidation(form, component["key"], api_value)

    @async_to_sync
    async def _assertAddressNLFrontendValidation(
        self, form: Form, ui_inputs: dict[str, str], expected_ui_error: str
    ) -> None:
        frontend_path = reverse("forms:form-detail", kwargs={"slug": form.slug})
        url = str(furl(self.live_server_url) / frontend_path)

        async with browser_page() as page:
            await page.goto(url)
            await page.get_by_role("button", name="Formulier starten").click()

            for field, value in ui_inputs.items():
                await page.fill(f"input[name='{field}']", value)

            # try to submit the step which should be invalid, so we expect this to
            # render the error message.
            await page.get_by_role("button", name="Volgende").click()

            await expect(page.get_by_text(expected_ui_error)).to_be_visible()

    def test_required_field(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "Required AddressNL",
            "validate": {"required": True},
            "deriveAddress": False,
        }

        self.assertAddressNLValidationIsAligned(
            component,
            ui_inputs={},
            api_value={
                "postcode": "",
                "houseNumber": "",
                "houseLetter": "",
                "houseNumberAddition": "",
            },
            expected_ui_error="Het verplichte veld Required AddressNL is niet ingevuld.",
        )

    def test_regex_failure(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL invalid regex",
            "deriveAddress": False,
        }

        test_cases = [
            (
                "postcode",
                {
                    "postcode": "1223456Wrong",
                    "houseNumber": "23",
                    "houseLetter": "A",
                    "houseNumberAddition": "",
                },
                "Postcode moet bestaan uit vier cijfers gevolgd door twee letters (bijv. 1234 AB).",
            ),
            (
                "houseNumber",
                {
                    "postcode": "1234AA",
                    "houseNumber": "A",
                    "houseLetter": "A",
                    "houseNumberAddition": "",
                },
                "Huisnummer moet een nummer zijn met maximaal 5 cijfers (bijv. 456).",
            ),
            (
                "houseLetter",
                {
                    "postcode": "1234AA",
                    "houseNumber": "33",
                    "houseLetter": "89",
                    "houseNumberAddition": "",
                },
                "Huisletter moet een enkele letter zijn.",
            ),
            (
                "houseNumberAddition",
                {
                    "postcode": "1234AA",
                    "houseNumber": "33",
                    "houseLetter": "A",
                    "houseNumberAddition": "9999A",
                },
                "Huisnummertoevoeging moet bestaan uit maximaal vier letters en cijfers.",
            ),
        ]

        for field_name, invalid_data, expected_error in test_cases:
            with self.subTest(field_name):
                self.assertAddressNLValidationIsAligned(
                    component,
                    ui_inputs=invalid_data,
                    api_value=invalid_data,
                    expected_ui_error=expected_error,
                )
