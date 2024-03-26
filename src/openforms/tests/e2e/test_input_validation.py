"""
Test that the input validation performed on the backend matches the one on the frontend.

The frontend/formio validation implementation is leading here.

Note that the actual test input/output is defined in the YAML-files in the
input_validation subdirectory.
"""

from pathlib import Path

from playwright.async_api import Page, expect

from openforms.formio.typing import Component, DateComponent, RadioComponent

from .input_validation_base import ValidationsTestCase

TEST_CASES = (Path(__file__).parent / "input_validation").resolve()


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
            "openForms": {"dataSrc": "manual"},  # type: ignore
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
            "key": "requiredLicenseplate",
            "label": "Required licenseplate",
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


class SinglePasswordTests(ValidationsTestCase):
    def test_required_field(self):
        component: Component = {
            "type": "password",
            "key": "requiredPassword",
            "label": "Required password",
            "validate": {"required": True},
        }

        self.assertValidationIsAligned(
            component,
            ui_input="",
            expected_ui_error="Het verplichte veld Required password is niet ingevuld.",
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
