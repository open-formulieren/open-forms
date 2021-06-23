"""
Bootstrap the environment.

Load the secrets from the .env file and store them in the environment, so
they are available for Django settings initialization.

.. warning::

    do NOT import anything Django related here, as this file needs to be loaded
    before Django is initialized.
"""
import os
import tempfile

import defusedxml
from dotenv import load_dotenv
from self_certifi import load_self_signed_certs as _load_self_signed_certs

EXTRA_CERTS_ENVVAR = "EXTRA_VERIFY_CERTS"


def setup_env():
    # install defusedxml - note that this monkeypatches the stdlib and is experimental.
    # xmltodict only supports defusedexpat, which hasn't been updated since python 3.3
    defusedxml.defuse_stdlib()

    # load the environment variables containing the secrets/config
    dotenv_path = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, ".env")
    load_dotenv(dotenv_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openforms.conf.dev")

    load_self_signed_certs()


def load_self_signed_certs() -> None:
    # create target directory for resulting combined certificate file
    target_dir = tempfile.mkdtemp()
    _load_self_signed_certs(target_dir)
