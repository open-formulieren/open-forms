from django.test import TestCase

from openforms.config.models import GlobalConfiguration


class PrivacyPolicyTests(TestCase):
    def test_render_default_privacy_label(self):
        conf = GlobalConfiguration.get_solo()
        conf.privacy_policy_url = "http://test-privacy-policy.nl"
        conf.save()

        label = conf.render_privacy_policy_label()

        self.assertEqual(
            'Ja, ik heb kennis genomen van het <a href="http://test-privacy-policy.nl">privacybeleid</a> '
            "en geef uitdrukkelijk toestemming voor het verwerken van de door mij opgegeven gegevens.",
            label,
        )

    def test_render_default_privacy_label_without_url(self):
        conf = GlobalConfiguration.get_solo()
        conf.privacy_policy_url = ""
        conf.save()

        label = conf.render_privacy_policy_label()

        self.assertEqual(
            "Ja, ik heb kennis genomen van het privacybeleid "
            "en geef uitdrukkelijk toestemming voor het verwerken van de door mij opgegeven gegevens.",
            label,
        )
