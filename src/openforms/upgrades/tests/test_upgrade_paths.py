import shutil
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from ..script_checks import BinScriptCheck

FILES_DIR = (Path(__file__).parent / "files").resolve()


class DjangoScriptTests(SimpleTestCase):
    def test_check_script(self):
        script_dir = Path(settings.BASE_DIR) / "bin"
        scripts = (
            ("check_pass", True),
            ("check_fail", False),
            ("check_error", False),
        )
        for script, expected_outcome in scripts:
            with self.subTest(script=script):
                src = FILES_DIR / f"{script}.py-tpl"
                dest = script_dir / f"{script}.py"
                shutil.copyfile(src, dest)
                self.addCleanup(dest.unlink)

                script_check = BinScriptCheck(script)

                self.assertEqual(script_check.execute(), expected_outcome)
