"""
Open Forms configuration and wrapper around ``vcr.py``.

There are essentially two approaches for testing the interaction with third party
services:

* Mocking the requests using ``requests_mock``
* Recording the real interactions and replaying those during tests

The tooling here assists with the second approach.

**Advantages of this approach**

- no bugs/mistakes in mock data/setup, as you are talking to a real service
- no need to manually update mocks or create them, you can automatically (re-)record
  the interactions
- if/when the remote service changes, you just run the same tests again while
  re-recording to capture the new behaviour

**Disadvantages**

- you need access to a real implementation and sharing those credentials in an open
  source project is a challenge
- there is a risk of exposing data you didn't mean to expose

**Strategies to avoid leaking information**

The host/domain of a particular service provided by a client to test with should not be
exposed, as these are internal domains. You can use `mitmproxy`_ to hide this, e.g.:

.. code-block:: bash

    mitmdump --mode reverse:https://example.com --ssl-insecure

**Specifying the record mode**

You can set the environment variable ``VCR_RECORD_MODE`` to any of the supported
`record modes`_.

.. _mitmproxy: https://github.com/mitmproxy/mitmproxy
.. _record modes: https://vcrpy.readthedocs.io/en/latest/usage.html#record-modes
"""

# once in dev, none in CI
import os
from pathlib import Path

from vcr.unittest import VCRMixin

RECORD_MODE = os.environ.get("VCR_RECORD_MODE", "none")


class OFVCRMixin(VCRMixin):
    """
    Mixin to use VCR in your unit tests.

    Using this mixin will result in HTTP requests/responses being recorded.
    """

    VCR_TEST_FILES: Path
    """
    A :class:`pathlib.Path` instance where the casettes should be stored.
    """

    def _get_cassette_library_dir(self):
        assert (
            self.VCR_TEST_FILES
        ), "You must define the `VCR_TEST_FILES` class attribute"
        return str(self.VCR_TEST_FILES / "vcr_cassettes" / self.__class__.__qualname__)

    def _get_vcr_kwargs(self):
        kwargs = super()._get_vcr_kwargs()
        kwargs.setdefault("record_mode", RECORD_MODE)
        return kwargs
