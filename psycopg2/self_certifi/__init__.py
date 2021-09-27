import os
import shutil
from typing import List, Optional

import certifi

__all__ = ("load_self_signed_certs", "EXTRA_CERTS_ENVVAR")


EXTRA_CERTS_ENVVAR = "EXTRA_VERIFY_CERTS"


def load_self_signed_certs(dest: str, paths: Optional[List[str]] = None) -> None:
    """
    Expose a CA-bundle with extra certificates to requests, based on certifi.

    The base bundle from certifi is taken (and copied) to the destination location.
    Any additional certificates are appended to this bundle, and finally the relevant
    environment variable for requests is set.

    You should call this function once in your application, before any requests are
    made.

    :arg dest: string, path where to write the new CA-bundle
    :arg paths: a list of paths to certificates to include. If not provided, the value
      is read from the environment variable ``EXTRA_VERIFY_CERTS``, which must be a
      comma-separated list of paths.
    """
    if paths is None:
        paths = os.environ.get(EXTRA_CERTS_ENVVAR, "")
        if not paths:
            return
        paths = paths.split(",")

    if "REQUESTS_CA_BUNDLE" in os.environ:
        raise ValueError(
            f"'{EXTRA_CERTS_ENVVAR}' and 'REQUESTS_CA_BUNDLE' conflict with each other."
        )

    # collect all extra certificates
    certs = []
    for path in paths:
        with open(path, "r") as certfile:
            certs.append(certfile.read())

    # copy certifi bundle to destination directory
    source = certifi.where()
    target = os.path.join(dest, os.path.basename(source))
    shutil.copy(source, target)

    with open(target, "a") as outfile:
        outfile.write("\n# Extra (self-signed) trusted certificates\n")
        outfile.write("\n\n".join(certs))

    # finally, set the REQUESTS_CA_BUNDLE environment variable
    os.environ["REQUESTS_CA_BUNDLE"] = target
