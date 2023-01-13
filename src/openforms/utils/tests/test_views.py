from django.test import TestCase
from django.urls import reverse


class ErrorViewTests(TestCase):
    def test_error_detail(self):
        exception_classes = (
            "NotFound",
            "ValidationError",
            "PermissionDenied",
            "RequestEntityTooLarge",
        )
        for clsname in exception_classes:
            with self.subTest(exception=clsname):
                url = reverse("error-detail", kwargs={"exception_class": clsname})

                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
