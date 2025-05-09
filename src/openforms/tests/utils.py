import contextlib
import cProfile
import io
import os
import pstats
import socket
import sys
from inspect import currentframe, getframeinfo
from pathlib import Path
from pstats import SortKey

from django.conf import settings

import structlog

NOOP_CACHES = {
    name: {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    for name in settings.CACHES.keys()
}

logger = structlog.stdlib.get_logger(__name__)


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


def is_github_actions() -> bool:
    """
    Determine if we're running in Github actions or not.

    See https://docs.github.com/en/actions/writing-workflows/\
        choosing-what-your-workflow-does/store-information-in-variables\
        #default-environment-variables
    """
    is_ci = os.environ.get("CI") == "true"
    is_gh_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    return is_ci and is_gh_actions


def log_flaky():
    """
    Log that a/the test is flaky.

    Call this function when you detect flakiness in a test. The result can be processed
    by Github workflows to add annotations, while retrying the test to not fail the
    build.
    """
    frame = currentframe()
    assert frame is not None
    assert frame.f_back is not None, (
        "You may only call log_flaky inside another function"
    )
    frame_info = getframeinfo(frame.f_back)
    relative_path = (
        Path(frame_info.filename).relative_to(Path(settings.BASE_DIR)).as_posix()
    )

    # on github actions, we can directly output in the right format to get annotations,
    # otherwise just plain log it in local dev
    if is_github_actions():
        print(
            f"::warning file={relative_path},line={frame_info.lineno}"
            f"::Flaky test: {frame_info.function}"
        )
    else:
        logger.warning(
            "flaky_test_detected",
            function=frame_info.function,
            file=relative_path,
            line=frame_info.lineno,
        )
