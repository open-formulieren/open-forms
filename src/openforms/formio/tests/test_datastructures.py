from unittest import TestCase

from openforms.formio.typing import Component, EditGridComponent

from ..datastructures import FormioConfiguration, FormioConfigurationWrapper, FormioData


class FormioDataTests(TestCase):
    def test_mimicks_dict_interface(self):
        formio_data = FormioData({"foo": "bar"})

        self.assertEqual(formio_data, {"foo": "bar"})
        self.assertEqual(formio_data["foo"], "bar")
        self.assertIsNone(formio_data.get("okay"))

        with self.assertRaises(KeyError):
            formio_data["bad_key_no_cookie"]

        with self.assertRaises(ValueError):
            FormioData(["bad type"])  # type: ignore

        with self.assertRaises(TypeError):
            FormioData(123)  # type: ignore

    def test_translate_dotted_lookup_paths(self):
        formio_data = FormioData({"foo": {"bar": "baz"}})

        with self.subTest("top-level key lookup"):
            self.assertEqual(formio_data["foo"], {"bar": "baz"})
            self.assertEqual(formio_data.get("foo"), {"bar": "baz"})

        with self.subTest("nested key lookup"):
            self.assertEqual(formio_data["foo.bar"], "baz")
            self.assertEqual(formio_data.get("foo.bar"), "baz")
            self.assertEqual(formio_data.get("foo.baz", "a default"), "a default")

    def test_translate_dotted_setter_paths(self):
        formio_data = FormioData({})

        formio_data["foo.bar"] = "baz"

        self.assertEqual(formio_data, {"foo": {"bar": "baz"}})

    def test_containment(self):
        formio_data = FormioData(
            {
                "top": "level",
                "container": {
                    "nested": "leaf",
                },
            }
        )

        with self.subTest("top level container"):
            self.assertTrue("top" in formio_data)

        with self.subTest("nested container"):
            self.assertTrue("container" in formio_data)

        with self.subTest("nested leaf"):
            self.assertTrue("container.nested" in formio_data)

        with self.subTest("top level absent"):
            self.assertFalse("absent" in formio_data)

        with self.subTest("nested absent"):
            self.assertFalse("container.absent" in formio_data)

    def test_initializing_with_dotted_paths_expands(self):
        formio_data = FormioData(
            {
                "container.nested1": "foo",
                "otherContainer.nested1": "bar",
                "container.nested2": "baz",
                "topLevel": True,
            }
        )

        expected = {
            "container": {
                "nested1": "foo",
                "nested2": "baz",
            },
            "otherContainer": {
                "nested1": "bar",
            },
            "topLevel": True,
        }

        self.assertEqual(formio_data, expected)

    def test_key_access_must_be_string(self):
        formio_data = FormioData({"foo": "bar"})

        bad_keys = (
            3,
            None,
            4.3,
            ("foo",),
        )

        for key in bad_keys:
            with self.assertRaises(TypeError):
                key in formio_data  # type: ignore

    def test_keyerror_for_absent_keys(self):
        formio_data = FormioData({})
        bad_keys = (
            "foo",
            "bar.baz",
        )

        for key in bad_keys:
            with (
                self.subTest(key=key),
                self.assertRaises(KeyError),
            ):
                formio_data[key]


class FormioConfigurationWrapperTests(TestCase):

    def test_editgrid_lookups_by_key(self):
        outer_textfield: Component = {
            "type": "textfield",
            "key": "outerTextfield",
            "label": "outer text field",
        }
        inner_textfield: Component = {
            "type": "textfield",
            "key": "innerTextfield",
            "label": "inner text field",
        }
        editgrid: EditGridComponent = {
            "type": "editgrid",
            "key": "editgrid",
            "label": "Repeating group",
            "components": [inner_textfield],
        }

        config: FormioConfiguration = {"components": [outer_textfield, editgrid]}
        config_wrapper = FormioConfigurationWrapper(config)

        with self.subTest("simple lookups"):
            self.assertIs(config_wrapper["editgrid"], editgrid)
            self.assertIs(config_wrapper["outerTextfield"], outer_textfield)
            self.assertIs(config_wrapper["innerTextfield"], inner_textfield)

        with self.subTest("nested editgrid lookup"):
            self.assertIs(config_wrapper["editgrid.innerTextfield"], inner_textfield)

    def test_nested_editgrids(self):
        inner_textfield: Component = {
            "type": "textfield",
            "key": "innerTextfield",
            "label": "inner text field",
        }
        inner_editgrid: EditGridComponent = {
            "type": "editgrid",
            "key": "innerEditgrid",
            "label": "Repeating group",
            "components": [inner_textfield],
        }
        outer_editgrid: EditGridComponent = {
            "type": "editgrid",
            "key": "outerEditgrid",
            "label": "Repeating group",
            "components": [inner_editgrid],
        }

        config: FormioConfiguration = {"components": [outer_editgrid]}
        config_wrapper = FormioConfigurationWrapper(config)

        self.assertIs(
            config_wrapper["outerEditgrid.innerEditgrid.innerTextfield"],
            inner_textfield,
        )
