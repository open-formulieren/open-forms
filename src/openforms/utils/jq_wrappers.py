"""
Wrappers for `jq`

We wrap `jq` with `subprocess.run` with an explicit timeout, because executing user
supplied jq expressions can lead to high resource consumption and potentially DoS.

Additionally, when running `jq` via the python library, it always has access to
all environment variables, which for the purpose that jq is used for in Open Forms
is not necessary at all.

Taken and adapted from Open Zaak (under the EUPL-1.2 license):
https://github.com/open-zaak/open-zaak/commit/15ac04ff5cf3f1a347532b9a42fe4de7401e8053#diff-7da238cfce5daa7f15620c7cb8a5efa87a6b850acee0dcc7e77b92c2e2217916
"""

import json
import subprocess

from django.conf import settings

from openforms.typing import JSONObject, JSONValue

_MAX_INPUT_BYTES = 4 * 1024 * 1024  # 4 MiB
_MAX_EXPRESSION_BYTES = 64 * 1024  # 64 KiB


class JQExecutionError(Exception):
    pass


class JQInvalidExpressionError(JQExecutionError):
    """The supplied expression is not valid jq."""


def validate_jq(expression: str) -> None:
    """
    Validate that expression is valid jq.

    Raises:
        JQInvalidExpressionError: If the expression is not valid jq.
        JQExecutionError: If jq cannot be executed or times out.
    """
    if len(expression.encode("utf-8")) > _MAX_EXPRESSION_BYTES:
        raise JQInvalidExpressionError("jq expression is too large")

    try:
        result = subprocess.run(
            ["/usr/bin/jq", "-c", expression],
            input="null",
            text=True,
            capture_output=True,
            timeout=settings.OPEN_FORMS_JQ_TIMEOUT,
            check=False,
            shell=False,  # to avoid shell injection
            env={},  # Isolate the env to not give access to all envvars
        )
    except subprocess.TimeoutExpired as exc:
        raise JQExecutionError("jq expression validation timed out") from exc
    except OSError as exc:  # pragma: no cover
        raise JQExecutionError("could not execute jq") from exc

    if result.returncode != 0:
        raise JQInvalidExpressionError(f"invalid jq expression: {result.stderr[:4000]}")


def run_jq(expression: str, data: JSONObject | None) -> JSONValue:
    """
    Execute a jq expression against data.

    This is run via `subprocess` with an explicit timeout, because executing user
    supplied jq expressions can lead to high resource consumption and potentially DoS.

    Additionally, when running `jq` via the python library, it always has access to
    all environment variables, which for the purpose that jq is used for in Open Zaak
    is not necessary at all.

    Raises:
        JQExecutionError: If jq cannot be executed successfully.
    """
    if len(expression.encode("utf-8")) > _MAX_EXPRESSION_BYTES:
        raise JQInvalidExpressionError("jq expression is too large")

    input_json = json.dumps(data)

    if len(input_json.encode("utf-8")) > _MAX_INPUT_BYTES:
        raise JQExecutionError("jq input is too large")

    try:
        result = subprocess.run(
            ["/usr/bin/jq", "-c", expression],
            input=input_json,
            text=True,
            capture_output=True,
            timeout=settings.OPEN_FORMS_JQ_TIMEOUT,
            check=False,
            shell=False,  # to avoid shell injection
            env={},  # Isolate the env to not give access to all envvars
        )
    except subprocess.TimeoutExpired as exc:
        raise JQExecutionError("jq execution timed out") from exc
    except OSError as exc:  # pragma: no cover
        raise JQExecutionError("could not execute jq") from exc

    if result.returncode != 0:  # pragma: no cover
        raise JQExecutionError(f"jq failed: {result.stderr[:4000]}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise JQExecutionError("jq returned invalid JSON") from exc
