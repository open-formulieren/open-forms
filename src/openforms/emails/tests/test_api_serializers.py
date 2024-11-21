from django.test import TestCase, override_settings, tag
from django.utils.translation import gettext as _

from ..api.serializers import ConfirmationEmailTemplateSerializer
from .factories import ConfirmationEmailTemplateFactory


def _find_error(errors: list, code: str, message: str):
    generator = (err for err in errors if err.code == code and str(err) == message)
    return next(generator, None)


@override_settings(LANGUAGES=[("nl", "Nederlands"), ("en", "English")])
class ConfirmationTemplateSerializerTests(TestCase):
    @tag("gh-2418")
    def test_validation_dependent_fields_with_translations(self):
        serializer = ConfirmationEmailTemplateSerializer(
            data={
                "translations": {
                    "nl": {
                        "subject": "",
                        "content": "Content without subject",
                    },
                    "en": {
                        "subject": "Subject without content",
                        "content": "",
                    },
                }
            }
        )

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)

        with self.subTest("nl specific errors"):
            errors = serializer.errors["translations"]["nl"]
            content_error = _find_error(
                errors["content"],
                code="invalid",
                message=_("Missing required template-tag {tag}").format(
                    tag="{% appointment_information %}"
                ),
            )
            self.assertIsNotNone(content_error)

    @tag("gh-2418")
    def test_valid_data(self):
        serializer = ConfirmationEmailTemplateSerializer(
            data={
                "translations": {
                    "nl": {
                        "subject": "Nederlands",
                        "content": "NL: {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                    "en": {
                        "subject": "English",
                        "content": "EN: {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                }
            }
        )

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)
        self.assertEqual(
            serializer.validated_data,
            {
                "subject_nl": "Nederlands",
                "subject_en": "English",
                "content_nl": "NL: {% appointment_information %} {% payment_information %} {% cosign_information %}",
                "content_en": "EN: {% appointment_information %} {% payment_information %} {% cosign_information %}",
                "cosign_subject_nl": "",
                "cosign_subject_en": "",
                "cosign_content_nl": "",
                "cosign_content_en": "",
            },
        )

    def test_can_update_model_fields(self):
        instance = ConfirmationEmailTemplateFactory.create(
            subject_nl="Foo",
            subject_en="Bar",
            content_nl="Welkom vriendjes en vriendinnetjes",
            content_en="This is fine",
        )
        serializer = ConfirmationEmailTemplateSerializer(
            instance=instance,
            data={
                "translations": {
                    "nl": {
                        "subject": "Nederlands",
                        "content": "NL: {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                    "en": {
                        "subject": "English",
                        "content": "EN: {% appointment_information %} {% payment_information %} {% cosign_information %}",
                    },
                }
            },
        )

        with self.subTest("Serializer validation"):
            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("Serializer saving"):
            serializer.save()

            instance.refresh_from_db()
            self.assertEqual(instance.subject_nl, "Nederlands")
            self.assertEqual(instance.subject_en, "English")

            self.assertEqual(
                instance.content_nl,
                "NL: {% appointment_information %} {% payment_information %} {% cosign_information %}",
            )
            self.assertEqual(
                instance.content_en,
                "EN: {% appointment_information %} {% payment_information %} {% cosign_information %}",
            )
