import contextlib
import sys
from pathlib import Path

from django.conf import settings
from django.utils.module_loading import import_string

import structlog
from upgrade_check.constraints import CodeCheck

logger = structlog.stdlib.get_logger(__name__)


@contextlib.contextmanager
def setup_scripts_env():
    """
    Set up the python path for the script execution, if any.

    Since the scripts in the ``bin`` dir are self-contained, we need to add the path
    to the python path to dynamically import the ``main`` function from the scripts.
    """
    bin_dir = str(Path(settings.BASE_DIR) / "bin")
    sys.path.insert(0, bin_dir)
    try:
        yield
    finally:
        sys.path.remove(bin_dir)


class BinScriptCheck(CodeCheck):
    """
    Code check that execeutes a script in the ``bin`` directory.
    """

    def __init__(self, script: str):
        self.script = script

    def execute(self) -> bool:
        with setup_scripts_env():
            main_func = import_string(f"{self.script}.main")
            try:
                result = main_func(skip_setup=True)
            except Exception as exc:
                logger.error("script_check_error", exc_info=exc)
                result = False
        del main_func  # reduce memory usage
        return True if result is None else result
