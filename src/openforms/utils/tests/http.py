"""
Use factory boy for fuzzing HTTP status codes.

Hypothesis results in random/flaky timeouts in CI (and sometimes even locally) which
is hard to debug. Using factory boy's fuzzy module allows us to test with randomness,
and if needed, we can extract the random seed from factory boy to reproduce potential
flakiness.
"""

from functools import partial

import factory.fuzzy

# Ranges taken from https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
_CLIENT_ERROR_STATUS_CODE = factory.fuzzy.FuzzyInteger(400, 451)
_SERVER_ERROR_STATUS_CODE = factory.fuzzy.FuzzyInteger(500, 511)


def _fuzzy_status_code_factory(fi: factory.fuzzy.FuzzyInteger):
    return partial(fi.evaluate, None, None, extra={})


fuzzy_client_error_status_code = _fuzzy_status_code_factory(_CLIENT_ERROR_STATUS_CODE)
fuzzy_server_error_status_code = _fuzzy_status_code_factory(_SERVER_ERROR_STATUS_CODE)
