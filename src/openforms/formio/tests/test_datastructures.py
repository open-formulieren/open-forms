from unittest import TestCase

from ..datastructures import FormioData


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
