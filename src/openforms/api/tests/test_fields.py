from django.test import TestCase

from rest_framework import serializers
from rest_framework.reverse import reverse

from openforms.forms.models import Form
from openforms.forms.tests.factories import FormFactory

from ..fields import RelatedFieldFromContext


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
