from django.test import SimpleTestCase

from ..script_checks import BinScriptCheck


class DjangoScriptTests(SimpleTestCase):
    def test_check_script(self):
        scripts = (
            ("check_pass", True),
            ("check_fail", False),
            ("check_error", False),
        )
        for script, expected_outcome in scripts:
            with self.subTest(script=script):
                script_check = BinScriptCheck(script)

                self.assertEqual(script_check.execute(), expected_outcome)
