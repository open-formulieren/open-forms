from django.test import SimpleTestCase

from glom import glom
from hypothesis import given, settings

from openforms.formio.service import iter_components
from openforms.formio.tests.search_strategies import (
    address_nl_component,
    any_component,
    bsn_component,
    checkbox_component,
    columns_component,
    content_component,
    cosign_v1_component,
    cosign_v2_component,
    currency_component,
    date_component,
    datetime_component,
    edit_grid_component,
    email_component,
    fieldset_component,
    file_component,
    iban_component,
    license_plate_component,
    map_component,
    np_family_members_component,
    number_component,
    password_component,
    phone_number_component,
    postcode_component,
    radio_component,
    select_component,
    selectboxes_component,
    signature_component,
    textarea_component,
    textfield_component,
    time_component,
)
from openforms.formio.typing import (
    ColumnsComponent,
    Component,
    ContentComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
)

from ..fd_translations_converter import process_component_tree


def _get_dummy_translations_store(component):
    translations_store = {"nl": {}}
    for comp in iter_components({"components": [component]}, recursive=True):
        if literal := comp.get("label"):
            translations_store["nl"][literal] = "Vertaald label"
    return translations_store


def do_processing(component):
    translations_store = _get_dummy_translations_store(component)
    process_component_tree([component], translations_store)


class ConverterRobustnessTests(SimpleTestCase):
    """
    Generate fixtures with hypothesis to check that our converter doesn't unexpectedly
    crashes on possibly weird but valid data.
    """

    def assertLabelsTranslated(self, component):
        for comp in iter_components({"components": [component]}, recursive=True):
            if not comp.get("label"):
                continue
            translation = glom(comp, "openForms.translations.nl.label", default="")
            self.assertEqual(translation, "Vertaald label")

    @given(any_component())
    # recursive structure, more expensive to draw examples
    @settings(max_examples=25, deadline=500)
    def test_any_component_is_properly_processed(self, component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(textfield_component())
    def test_textfield_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(email_component())
    def test_email_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(date_component())
    def test_date_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(datetime_component())
    def test_datetime_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(time_component())
    def test_time_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(phone_number_component())
    def test_phone_number_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(file_component())
    def test_file_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(textarea_component())
    def test_textarea_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(number_component())
    def test_number_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(select_component())
    def test_select_component(self, component: SelectComponent):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(checkbox_component())
    def test_checkbox_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(selectboxes_component())
    def test_selectboxes_component(self, component: SelectBoxesComponent):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(currency_component())
    def test_currency_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(radio_component())
    def test_radio_component(self, component: RadioComponent):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(iban_component())
    def test_iban_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(license_plate_component())
    def test_license_plate_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(bsn_component())
    def test_bsn_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(address_nl_component())
    def test_address_nl_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(np_family_members_component())
    def test_np_family_members_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(signature_component())
    def test_signature_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(cosign_v2_component())
    def test_cosign_v2_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(map_component())
    def test_map_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(postcode_component())
    def test_postcode_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(password_component())
    def test_password_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(cosign_v1_component())
    def test_cosign_v1_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(content_component())
    def test_content_component(self, component: ContentComponent):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(edit_grid_component())
    # recursive structure, more expensive to draw examples
    @settings(max_examples=10, deadline=500)
    def test_edit_grid_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(fieldset_component())
    # recursive structure, more expensive to draw examples
    @settings(max_examples=10, deadline=500)
    def test_fieldset_component(self, component: Component):
        do_processing(component)

        self.assertLabelsTranslated(component)

    @given(columns_component())
    # recursive structure, more expensive to draw examples
    @settings(max_examples=10, deadline=500)
    def test_columns_component(self, component: ColumnsComponent):
        do_processing(component)

        self.assertLabelsTranslated(component)
