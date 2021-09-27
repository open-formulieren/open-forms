import tempfile

from django.test import override_settings


def temp_private_root():
    # Convenience decorator/context manager to use a temporary directory as
    # PRIVATE_MEDIA_ROOT.
    tmpdir = tempfile.mkdtemp()
    return override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir)
