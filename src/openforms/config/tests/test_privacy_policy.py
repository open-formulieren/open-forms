from django.test import TestCase, override_settings

from openforms.config.models import GlobalConfiguration


@override_settings(LANGUAGE_CODE="en")
class PrivacyPolicyTests(TestCase):
    def test_render_privacy_label(self):
        conf = GlobalConfiguration.get_solo()
        conf.privacy_policy_label = "I read the {% privacy_policy %} and agree."
        conf.privacy_policy_url = "http://test-privacy-policy.nl"
        conf.save()

        label = conf.render_privacy_policy_label()

        self.assertHTMLEqual(
            'I read the <a href="http://test-privacy-policy.nl" target="_blank" '
            'rel="noreferrer noopener">privacy policy</a> and agree.',
            label,
        )

    def test_render_privacy_label_without_url(self):
        conf = GlobalConfiguration.get_solo()
        conf.privacy_policy_label = "I read the {% privacy_policy %} and agree."
        conf.privacy_policy_url = ""
        conf.save()

        label = conf.render_privacy_policy_label()

        self.assertEqual(
            "I read the  and agree.",
            label,
        )
