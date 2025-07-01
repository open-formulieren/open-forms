"""
Test runner with reproducible randomness.

To reproduce tests, set the ``TEST_RANDOM_STATE`` envvar from CI output. To report the
random state locally, set the ``TEST_REPORT_RANDOM_STATE`` envvar to ``true``:

..code-block:: bash

    export TEST_REPORT_RANDOM_STATE=true
    src/manage.py test src

See https://factoryboy.readthedocs.io/en/stable/recipes.html#using-reproducible-randomness
"""

import base64
import os
import pickle

from django.test.runner import DiscoverRunner

import factory.random


def _setup_random_state():
    state = os.environ.get("TEST_RANDOM_STATE")
    report_random_state = (
        os.environ.get("TEST_REPORT_RANDOM_STATE", "").lower() == "true"
    )
    decoded_state = None

    if state:
        try:
            decoded_state = pickle.loads(base64.b64decode(state.encode("ascii")))
        except ValueError:
            pass

    if decoded_state:
        factory.random.set_random_state(decoded_state)
    elif report_random_state:
        encoded_state = base64.b64encode(
            pickle.dumps(factory.random.get_random_state())
        )
        print("Current random state: {}".format(encoded_state.decode("ascii")))


class RandomStateRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        _setup_random_state()
        super().setup_test_environment(**kwargs)
