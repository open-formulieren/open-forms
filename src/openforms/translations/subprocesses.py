import contextlib
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models.fields.files import FieldFile

# make sure the right path is used for the subporcess (different paths are used based on
# the environment)
PROJECT_ROOT = settings.DJANGO_PROJECT_DIR.parent.parent
FORMATJS_BIN = PROJECT_ROOT / "node_modules" / ".bin" / "formatjs"


@contextlib.contextmanager
def ensure_input_file_exists_on_disk(input_file: FieldFile) -> Generator[str]:
    # ensure that the input file exists on disk, in case non-filesystem storage backends
    # are used
    if isinstance(input_file.storage, FileSystemStorage):
        yield input_file.path
    else:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json") as tmp_input_file:
            # copy the contents to the temp file
            input_file.seek(0)
            for chunk in input_file.chunks():
                tmp_input_file.write(chunk)
            tmp_input_file.flush()
            yield tmp_input_file.name


def compile_messages_file(input_file: FieldFile) -> tuple[bool, str]:
    """
    Compiles a messages JSON file using formatjs as a subprocess.

    :param input_file: The model field containing the input file.

    Returns:
        (True, compiled_json) on success
        (False, error_message) on failure
    """
    with ensure_input_file_exists_on_disk(input_file) as input_path:
        with (
            tempfile.NamedTemporaryFile(
                mode="r",
                suffix=".json",
                encoding="utf-8",
                delete=False,
            ) as output_tmp,
        ):
            output_path = output_tmp.name

        try:
            subprocess.run(
                [
                    str(FORMATJS_BIN),
                    "compile",
                    input_path,
                    "--ast",
                    "--out-file",
                    output_path,
                ],
                stderr=subprocess.PIPE,
                check=True,
            )
            with open(output_path, encoding="utf-8") as f:
                compiled_json: str = f.read()

            return True, compiled_json
        except subprocess.CalledProcessError as exc:
            error_msg: str = exc.stderr.decode("utf-8").strip()
            return False, error_msg

        finally:
            # Clean up the temporary file
            Path(output_path).unlink(missing_ok=True)
