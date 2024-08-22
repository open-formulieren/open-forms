from django.test import SimpleTestCase, override_settings

from .factories import EmailVerificationFactory


class EmailVerificationModelTests(SimpleTestCase):

    @override_settings(LANGUAGE_CODE="en")
    def test_string_representation(self):
        with self.subTest("unverified"):
            unverified = EmailVerificationFactory.build(
                email="info@opengem.nl", verified_on=None, component_key="email"
            )
            self.assertEqual(
                str(unverified), "info@opengem.nl (component 'email'): not verified"
            )

        with self.subTest("verified"):
            verified = EmailVerificationFactory.build(
                email="info@opengem.nl", verified=True, component_key="email"
            )
            self.assertEqual(
                str(verified), "info@opengem.nl (component 'email'): verified"
            )
