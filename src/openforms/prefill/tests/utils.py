from contextlib import contextmanager
from unittest.mock import patch

from ..contrib.demo.plugin import DemoPrefill
from ..registry import Registry


def get_test_register() -> Registry:
    register = Registry()
    register("demo")(DemoPrefill)
    return register


@contextmanager
def patch_prefill_registry(new_register: Registry | None = None):
    if new_register is None:
        new_register = get_test_register()

    with (
        patch("openforms.prefill.service.default_register", new=new_register),
        patch(
            "openforms.forms.api.serializers.form_variable.register", new=new_register
        ),
    ):
        yield
