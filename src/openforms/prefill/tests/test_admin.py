from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory

from ..models import PrefillConfig


class PrefillConfigTests(WebTest):
    def test_repr(self):
        instance = PrefillConfig()

        self.assertEqual(str(instance), PrefillConfig._meta.verbose_name)

    def test_registry_list_for_defaults(self):
        user = SuperUserFactory.create()
        (
            config,
            _,
        ) = (
            PrefillConfig.objects.get_or_create()
        )  # not using get_solo for cache reasons
        url = reverse("admin:prefill_prefillconfig_change", args=(config.pk,))

        response = self.app.get(url, user=user)

        # check that it's a dropdown-like widget with options/choices
        self.assertGreater(len(response.form["default_person_plugin"].options), 1)
        self.assertGreater(len(response.form["default_company_plugin"].options), 1)
