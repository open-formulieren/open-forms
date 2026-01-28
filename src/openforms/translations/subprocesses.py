import subprocess
import tempfile
from pathlib import Path


def compile_messages_file(input_path: str) -> tuple[bool, str | None]:
    """
    Compiles a messages JSON file using formatjs as a subprocess.

    Returns:
        (True, compiled_json) on success
        (False, error_message) on failure
    """
    with tempfile.NamedTemporaryFile(
        mode="r",
        suffix=".json",
        encoding="utf-8",
        delete=False,
    ) as output_tmp:
        output_path = output_tmp.name

    try:
        subprocess.run(
            [
                "npx",
                "formatjs",
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
        # Clean up the temporary file if it exists
        if output_path and (temp_output_path := Path(output_path)).exists():
            temp_output_path.unlink(missing_ok=True)
