import contextlib
import cProfile
import io
import os
import pstats
import socket
from pstats import SortKey

from django.conf import settings
from django.test import override_settings

NOOP_CACHES = {
    name: {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    for name in settings.CACHES.keys()
}


disable_2fa = override_settings(TWO_FACTOR_PATCH_ADMIN=False)


def can_connect(hostname: str):
    # adapted from https://stackoverflow.com/a/28752285
    hostname, port = hostname.split(":")
    try:
        host = socket.gethostbyname(hostname)
        s = socket.create_connection((host, port), 2)
        s.close()
        return True
    except Exception:
        return False


@contextlib.contextmanager
def supress_output(stdchannel, dest_filename):
    """
    A context manager to temporarily redirect stdout or stderr

    e.g.:


    with supress_output(sys.stderr, os.devnull):
        if compiler.has_function('clock_gettime', libraries=['rt']):
            libraries.append('rt')

    Taken from https://stackoverflow.com/a/17753573
    """

    oldstdchannel = os.dup(stdchannel.fileno())
    dest_file = open(dest_filename, "w")
    os.dup2(dest_file.fileno(), stdchannel.fileno())
    try:
        yield
    finally:
        os.dup2(oldstdchannel, stdchannel.fileno())
        dest_file.close()


@contextlib.contextmanager
def c_profile(sort_by=SortKey.CUMULATIVE):  # pragma: no cover
    """
    Profile a block of code with cProfile.
    """
    with cProfile.Profile() as pr:
        yield
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
        ps.print_stats()
        print(s.getvalue())
