import contextlib
import cProfile
import io
import logging
import os
import pstats
import socket
import sys
from inspect import currentframe, getframeinfo
from pathlib import Path
from pstats import SortKey

from django.conf import settings

NOOP_CACHES = {
    name: {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    for name in settings.CACHES.keys()
}

flaky_test_logger = logging.getLogger("flaky_tests")


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
def profile_outfile():
    # On github CI, write to the step summary
    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if not github_summary:
        yield sys.stdout
    else:
        with Path(github_summary).open("a") as outfile:
            outfile.write("```\n")
            yield outfile
            outfile.write("```")
            outfile.write("\n\n")


@contextlib.contextmanager
def c_profile(sort_by=SortKey.CUMULATIVE):  # pragma: no cover
    """
    Profile a block of code with cProfile.
    """
    with profile_outfile() as outfile:
        with cProfile.Profile() as pr:
            yield
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
            ps.print_stats()
            print(s.getvalue(), file=outfile)


def log_flaky():
    """
    Log that a/the test is flaky.

    Call this function when you detect flakiness in a test. The result can be processed
    by Github workflows to add annotations, while retrying the test to not fail the
    build.
    """
    frame = currentframe()
    assert frame is not None
    assert (
        frame.f_back is not None
    ), "You may only call log_flaky inside another function"
    frame_info = getframeinfo(frame.f_back)
    relative_path = Path(frame_info.filename).relative_to(Path(settings.BASE_DIR))
    flaky_test_logger.warning(
        "Flaky test: %s",
        frame_info.function,
        extra={
            "file": relative_path,
            "line": frame_info.lineno,
        },
    )
