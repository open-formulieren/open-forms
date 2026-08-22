from unittest import TestCase

from formio_types import EditGrid, Fieldset, TextField
from openforms.formio.typing import Component, EditGridComponent, FieldsetComponent

from ..datastructures import FormioConfig, FormioData


class FormioDataTests(TestCase):
    def test_mimicks_dict_interface(self):
        formio_data = FormioData({"foo": "bar"})

        self.assertEqual(formio_data.data, {"foo": "bar"})
        self.assertEqual(formio_data["foo"], "bar")
        self.assertIsNone(formio_data.get("okay"))

        with self.assertRaises(KeyError):
            formio_data["bad_key_no_cookie"]

        with self.assertRaises(ValueError):
            FormioData(["bad type"])  # type: ignore

        with self.assertRaises(TypeError):
            FormioData(123)  # type: ignore

    def test_translate_dotted_lookup_paths(self):
        formio_data = FormioData(
            {"foo": {"bar": "baz"}, "key": "value", "list": [{"foo": "bar"}]}
        )

        with self.subTest("top-level key lookup"):
            self.assertEqual(formio_data["foo"], {"bar": "baz"})
            self.assertEqual(formio_data.get("foo"), {"bar": "baz"})

        with self.subTest("nested key lookup"):
            self.assertEqual(formio_data["foo.bar"], "baz")
            self.assertEqual(formio_data.get("foo.bar"), "baz")
            self.assertEqual(formio_data.get("foo.baz", "a default"), "a default")

        with self.subTest("nested absent on top level"), self.assertRaises(KeyError):
            formio_data["key.absent"]

        with self.subTest("list access"):
            self.assertEqual(formio_data["list.0.foo"], "bar")

        with self.subTest("list access out of range"), self.assertRaises(KeyError):
            formio_data["list.1.foo"]

        with self.subTest("list access on string"), self.assertRaises(KeyError):
            formio_data["list.string_index"]

    def test_translate_dotted_setter_paths(self):
        formio_data = FormioData({})

        formio_data["foo.bar"] = "baz"

        self.assertEqual(formio_data.data, {"foo": {"bar": "baz"}})

    def test_containment(self):
        formio_data = FormioData(
            {
                "top": "level",
                "container": {
                    "nested": "leaf",
                },
                "list": [{"foo": "bar"}],
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

        with self.subTest("nested absent on top level"):
            self.assertFalse("top.absent" in formio_data)

        with self.subTest("nested list"):
            self.assertTrue("list.0.foo" in formio_data)

        with self.subTest("nested list absent"):
            self.assertFalse("list.4.foo" in formio_data)

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

        self.assertEqual(formio_data.data, expected)

    def test_key_access_must_be_string(self):
        formio_data = FormioData({"foo": "bar"})

        bad_keys = (
            3,
            None,
            4.3,
            ("foo",),
        )

        for key in bad_keys:
            with self.assertRaises(Exception) as cm:
                key in formio_data  # type: ignore  # noqa: B015
                self.assertIsInstance(cm.exception, AssertionError | TypeError)

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

    def test_ensure_nested_structure(self):
        data = FormioData(
            {"foo": {"bar": "baz"}, "key": "value", "list": [{"foo": {"bar": "baz"}}]}
        )

        with self.subTest("items"):
            expected = (
                ("foo", {"bar": "baz"}),
                ("key", "value"),
                ("list", [{"foo": {"bar": "baz"}}]),
            )
            for (key, value), (key_expected, value_expected) in zip(
                expected, data.items(), strict=False
            ):
                self.assertEqual(key, key_expected)
                self.assertEqual(value, value_expected)

        with self.subTest("keys and values"):
            self.assertEqual(list(data.keys()), ["foo", "key", "list"])
            self.assertEqual(
                list(data.values()),
                [{"bar": "baz"}, "value", [{"foo": {"bar": "baz"}}]],
            )

        with self.subTest("**"):
            self.assertEqual(
                {**data},
                {
                    "foo": {"bar": "baz"},
                    "key": "value",
                    "list": [{"foo": {"bar": "baz"}}],
                },
            )

    def test_pop_items(self):
        data = FormioData(
            {
                "foo": {"bar": "baz"},
                "key": "value",
                "list": ["a", {"foo": {"bar": "baz"}}],
            },
        )

        with self.subTest("pop normal"):
            value = data.pop("key")
            self.assertEqual(value, "value")
            self.assertRaises(KeyError, lambda: data["key"])

        with self.subTest("pop nested"):
            value = data.pop("foo.bar")
            self.assertEqual(value, "baz")
            self.assertEqual(data["foo"], {})

        with self.subTest("pop list out of range"):
            value = data.pop("list.5", "default")
            self.assertEqual(value, "default")
            self.assertEqual(data["list"], ["a", {"foo": {"bar": "baz"}}])

        with self.subTest("pop list"):
            value = data.pop("list.1")
            self.assertEqual(value, {"foo": {"bar": "baz"}})
            self.assertEqual(data["list"], ["a"])

        with self.subTest("pop missing"):
            value = data.pop("non.existing", None)
            self.assertIsNone(value)

    def test_del_items(self):
        data = FormioData(
            {
                "foo": {"bar": "baz"},
                "key": "value",
                "list": ["a", {"foo": {"bar": "baz"}}],
                "simply": "lovely",
            },
        )

        with self.subTest("del normal"):
            del data["key"]
            self.assertRaises(KeyError, lambda: data["key"])

        with self.subTest("del nested"):
            del data["foo.bar"]
            self.assertEqual(data["foo"], {})

        with self.subTest("del list"):
            del data["list.1"]
            self.assertEqual(data["list"], ["a"])

        with self.subTest("del list out of range"), self.assertRaises(KeyError):
            del data["list.5"]

        with self.subTest("del missing"), self.assertRaises(KeyError):
            del data["non.existing"]

        with self.subTest("del partially missing"), self.assertRaises(KeyError):
            del data["foo.non_existing"]

        with self.subTest("del on string"):
            with self.assertRaises(KeyError):
                del data["simply.3"]
            self.assertEqual(data["simply"], "lovely")


class FormioConfigTests(TestCase):
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
            "groupLabel": "Item",
            "components": [inner_textfield],
        }

        formio_config = FormioConfig(
            name="test", components=[outer_textfield, editgrid]
        )

        with self.subTest("top level lookups"):
            top_level_editgrid = formio_config["editgrid"]

            self.assertIsInstance(top_level_editgrid, EditGrid)
            self.assertEqual(top_level_editgrid.key, "editgrid")

            self.assertIn("outerTextfield", formio_config)
            self.assertNotIn("innerTextfield", formio_config)

        with self.subTest("nested editgrid lookup"):
            self.assertIn("editgrid.innerTextfield", formio_config)

            nested_textfield = formio_config["editgrid.innerTextfield"]
            self.assertIsInstance(nested_textfield, TextField)

    def test_editgrid_with_layout_components_inside_used_namespaced_key_lookup(self):
        inner_textfield: Component = {
            "type": "textfield",
            "key": "innerTextfield",
            "label": "inner text field",
        }
        fieldset: FieldsetComponent = {
            "type": "fieldset",
            "key": "fieldset",
            "label": "Fieldset",
            "components": [inner_textfield],
        }
        editgrid: EditGridComponent = {
            "type": "editgrid",
            "key": "editgrid",
            "label": "Repeating group",
            "groupLabel": "Item",
            "components": [fieldset],
        }
        formio_config = FormioConfig(name="test", components=[editgrid])

        nested_fieldset = formio_config["editgrid.fieldset"]
        self.assertIsInstance(nested_fieldset, Fieldset)
        nested_textfield = formio_config["editgrid.innerTextfield"]
        self.assertIsInstance(nested_textfield, TextField)

    def test_nested_editgrids(self):
        inner_textfield: Component = {
            "type": "textfield",
            "key": "innerTextfield",
            "label": "inner text field",
        }
        inner_editgrid: EditGridComponent = {
            "type": "editgrid",
            "key": "child",
            "label": "Repeating group",
            "groupLabel": "Item",
            "components": [inner_textfield],
        }
        outer_textfield: Component = {
            "type": "textfield",
            "key": "outerTextfield",
            "label": "outer text field",
        }
        outer_editgrid: EditGridComponent = {
            "type": "editgrid",
            "key": "parent",
            "label": "Repeating group",
            "groupLabel": "Item",
            "components": [outer_textfield, inner_editgrid],
        }

        formio_config = FormioConfig(name="test", components=[outer_editgrid])

        editgrid = formio_config["parent"]
        self.assertIsInstance(editgrid, EditGrid)
        text_in_parent_editgrid = formio_config["parent.outerTextfield"]
        self.assertIsInstance(text_in_parent_editgrid, TextField)
        child_editgrid = formio_config["parent.child"]
        self.assertIsInstance(child_editgrid, EditGrid)
        self.assertEqual(child_editgrid.key, "child")
        text_in_child_editgrid = formio_config["parent.child.innerTextfield"]
        self.assertIsInstance(text_in_child_editgrid, TextField)
        self.assertEqual(text_in_child_editgrid.key, "innerTextfield")
