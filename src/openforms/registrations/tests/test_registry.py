from functools import partial

from django.test import SimpleTestCase

from rest_framework import serializers

from ..registry import Registry


class OptionsSerializer(serializers.Serializer):
    pass


def dummy_callback(submission, opts):
    pass


class RegistryTests(SimpleTestCase):
    def test_register_function(self):
        register = Registry()

        register(
            unique_identifier="cb1",
            name="Test callback",
            configuration_options=OptionsSerializer,
        )(dummy_callback)

        plugin = register["cb1"]

        self.assertEqual(plugin.unique_identifier, "cb1")
        self.assertEqual(plugin.callback, dummy_callback)
        self.assertEqual(plugin.name, "Test callback")

    def test_duplicate_identifier(self):
        register = Registry()
        _register = partial(
            register, name="Test callback", configuration_options=OptionsSerializer
        )
        _register(unique_identifier="cb1")(dummy_callback)

        def other_callback(submission, opts):
            pass

        with self.assertRaisesMessage(
            ValueError, "The unique identifier 'cb1' is already present in the registry"
        ):
            _register(unique_identifier="cb1")(other_callback)

    def test_bad_typehint(self):
        register = Registry()

        def callback(sub: int, opts):
            pass

        with self.assertRaisesMessage(
            TypeError, "The 'sub' typehint does not appear to be a Submission."
        ):
            register(
                unique_identifier="cb1",
                name="Test callback",
                configuration_options=OptionsSerializer,
            )(callback)

    def test_bad_signature(self):

        register = Registry()

        def bad_1():
            pass

        def bad_2(arg1):
            pass

        def bad_3(arg1, arg2, arg3):
            pass

        for cb in (bad_1, bad_2):
            with self.subTest(callback=cb):
                with self.assertRaisesMessage(
                    TypeError,
                    "A callback must take exactly two arguments - an instance of 'submissions.Submission' and "
                    "the options object.",
                ):
                    register(
                        cb.__name__,
                        name="bad callback",
                        configuration_options=OptionsSerializer,
                    )(cb)
