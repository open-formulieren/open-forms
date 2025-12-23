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

If it is a SOAP service that requires client certificates for in-band messages,
the ``--set client_certs=DIRECTORY|FILE`` flag of `mitmproxy`_ to setup mTLS can't help.
E.g. the Suwinet client (and prefill plugin) tests rewrite urls in requests and responses
with a url from an environment variable (see dotenv-example).

**Specifying the record mode**

You can set the environment variable ``VCR_RECORD_MODE`` to any of the supported
`record modes`_.

.. note::

    When you use VCR for tests with obfuscated URLs or credentials (or any sensitive
    data in general), you must document this information (in Taiga) so that other
    people have all the necessary information/steps at hand to re-record cassettes.

    Re-recording is done as part of the :ref:`release process<developers_releases>`.

.. _mitmproxy: https://github.com/mitmproxy/mitmproxy
.. _record modes: https://vcrpy.readthedocs.io/en/latest/usage.html#record-modes
"""

# once in dev, none in CI
import inspect
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from maykin_common.vcr import VCRMixin
from vcr.config import VCR

RECORD_MODE = os.environ.get("VCR_RECORD_MODE", "none")


def get_default_path_for_cls(klass: type) -> Path:
    class_name = klass.__qualname__
    path = Path(inspect.getfile(klass))
    return path.parent / "vcr_cassettes" / path.stem / class_name


class OFVCRMixin(VCRMixin):
    """
    Mixin to use VCR in your unit tests.

    Using this mixin will result in HTTP requests/responses being recorded.
    """

    def _get_cassette_library_dir(self):
        if self.VCR_TEST_FILES:
            return super()._get_cassette_library_dir()
        # skip intermediate directories and keep cassettes close to the test module
        return str(get_default_path_for_cls(self.__class__))


@contextmanager
def with_setup_test_data_vcr(cls: type) -> Iterator[None]:
    """
    Context manager to explicitly use VCR (inside setUpTestData for instance)

    :param base_path: The base directory for VCR test files.
    :param class_name: The qualified name of the test class.
    """
    base_path = get_default_path_for_cls(cls)
    with VCR().use_cassette(base_path / "setUpTestData.yaml"):
        yield
