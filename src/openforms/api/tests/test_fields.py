import base64
from typing import Literal

from django.core.files import File
from django.test import TestCase

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory
from unittest_parametrize import ParametrizedTestCase, parametrize

from openforms.forms.models import Form
from openforms.forms.tests.factories import FormFactory

from ..fields import Base64ImageField, RelatedFieldFromContext

factory = APIRequestFactory()


class RelatedFieldFromContextSerializer(serializers.Serializer):
    form = RelatedFieldFromContext(
        queryset=Form.objects.all(),
        view_name="api:form-detail",
        lookup_field="uuid",
        lookup_url_kwarg="uuid_or_slug",
        context_name="forms",
    )


class RelatedFieldFromContextTests(TestCase):
    def test_valid_lookup(self):
        form = FormFactory.create()
        serializer = RelatedFieldFromContextSerializer(
            data={
                "form": reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid}),
            },
            context={"forms": {str(form.uuid): form}},
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid_lookup(self):
        form1 = FormFactory.create()
        form2 = FormFactory.create()
        serializer = RelatedFieldFromContextSerializer(
            data={
                "form": reverse("api:form-detail", kwargs={"uuid_or_slug": form1.uuid}),
            },
            context={"forms": {str(form2.uuid): form2}},
        )

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertEqual(serializer.errors["form"][0].code, "does_not_exist")

    def test_wrong_object(self):
        form1 = FormFactory.create()
        form2 = FormFactory.create()
        serializer = RelatedFieldFromContextSerializer(
            data={
                "form": reverse("api:form-detail", kwargs={"uuid_or_slug": form1.uuid}),
            },
            context={
                "forms": {
                    str(form1.uuid): form2,
                    str(form2.uuid): form1,
                }
            },
        )

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertEqual(serializer.errors["form"][0].code, "incorrect_match")


class Base64ImageFieldSerializer(serializers.Serializer):
    image = Base64ImageField(
        source="help_dialog_image",
        required=False,
        allow_null=True,
        allow_empty_file=True,
    )


class Base64ImageFieldTests(ParametrizedTestCase, TestCase):
    def setUp(self):
        super().setUp()

        self.addCleanup(self._delete_images)

    def _delete_images(self):
        for form in Form.objects.exclude(help_dialog_image=""):
            form.help_dialog_image.storage.delete(form.help_dialog_image.name)

    def test_serializer_output_no_image_configured(self):
        form = FormFactory.build(help_dialog_image="")
        request = factory.get("/irrelevant")

        serializer = Base64ImageFieldSerializer(
            instance=form, context={"request": request}
        )

        self.assertIsNone(serializer.data["image"])

    def test_serializer_output_with_image_configured(self):
        form = FormFactory.build(with_help_dialog_image=True)
        assert form.help_dialog_image
        request = factory.get("/irrelevant")

        serializer = Base64ImageFieldSerializer(
            instance=form, context={"request": request}
        )

        self.assertTrue(serializer.data["image"].startswith("http://testserver/media/"))

    def test_field_accepts_base64_image_data(self):
        single_pixel_data = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
            b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
            b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
        ).decode("ascii")

        serializer = Base64ImageFieldSerializer(data={"image": single_pixel_data})

        self.assertTrue(serializer.is_valid())
        self.assertIsInstance(
            serializer.validated_data["help_dialog_image"],
            File,
        )

    def test_field_accepts_null_to_clear_image_field(self):
        serializer = Base64ImageFieldSerializer(data={"image": None})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["help_dialog_image"], "")

    def test_field_accepts_empty_string_to_leave_field_untouched(self):
        serializer = Base64ImageFieldSerializer(data={"image": ""})

        self.assertTrue(serializer.is_valid())
        # field not present -> won't update model
        self.assertEqual(serializer.validated_data, {})

    @parametrize("value", ("", None))
    def test_not_valid_if_empty_file_not_allowed(self, value: Literal[""] | None):
        class TestSerializer(serializers.Serializer):
            image = Base64ImageField(allow_null=False, allow_empty_file=False)

        serializer = TestSerializer(data={"image": value})

        self.assertFalse(serializer.is_valid())

    def test_rejects_badly_formatted_base64_data(self):
        serializer = Base64ImageFieldSerializer(data={"image": "uh"})

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["image"][0].code, "invalid")

    def test_rejects_non_image_data(self):
        plain_text = b"this should not be accepted"
        data = base64.b64encode(plain_text).decode("ascii")

        serializer = Base64ImageFieldSerializer(data={"image": data})

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["image"][0].code, "invalid")

    def test_rejects_garbage(self):
        plain_text = b"\x89GNP\r\n\x1a\n\x00\x00\x00\rRDHI"
        data = base64.b64encode(plain_text).decode("ascii")

        serializer = Base64ImageFieldSerializer(data={"image": data})

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors["image"][0].code, "invalid")
