from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO


@contextmanager
def capture_output():
    outfile = StringIO()
    with (
        redirect_stdout(outfile),
        redirect_stderr(outfile),
    ):
        yield outfile
