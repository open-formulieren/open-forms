import logging
from typing import List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_PATH_PARAMETERS = {"version": "1"}

TYPE_ARRAY = "array"

DEFAULT_SERVERS = [
    {
        "url": "/",
    }
]


def get_operation_url(
    spec: dict, operation: str, pattern_only=False, base_url: str = None, **kwargs
) -> str:
    if base_url:
        url = base_url
    else:
        # servers is optional, see https://swagger.io/specification/#openapi-object
        servers = spec.get("servers") or DEFAULT_SERVERS
        url = servers[0]["url"]

    base_path = urlparse(url).path

    for path, methods in spec["paths"].items():
        for name, method in methods.items():
            if name == "parameters":
                continue

            if method["operationId"] == operation:
                format_kwargs = DEFAULT_PATH_PARAMETERS.copy()
                format_kwargs.update(**kwargs)
                if not pattern_only:
                    path = path.format(**format_kwargs)

                # if both base_path ends with a slash and path starts with one,
                # we need to join them together correctly, so drop one slash
                if base_path.endswith("/") and path.startswith("/"):
                    path = path[1:]

                return "{base_path}{path}".format(base_path=base_path, path=path)

    raise ValueError("Operation {operation} not found".format(operation=operation))


def path_to_bits(path: str, transform=reversed) -> list:
    """
    Split a path into a list of parts.

    By default the parts are returned in reverse order to match two paths
    by their ends and discard any mismatching prefixes.
    """
    return [bit for bit in transform(path.split("/")) if bit]


def extract_params(url: str, pattern: str) -> dict:
    """
    Given an actual url and a pattern, extract the matching parameters.

    Example:

    >>> pattern = '/api/v1/zaken/{uuid}'
    >>> url = 'https://example.com/zrc/api/v1/zaken/1234'
    >>> extract_params(url, pattern)
    {'uuid': '1234'}
    """
    path_url = urlparse(url).path
    path_pattern = urlparse(pattern).path

    # pattern should be shortest, since actual urls may be hosted on a subpath
    pattern_bits = path_to_bits(path_pattern)
    url_bits = path_to_bits(path_url)[: len(pattern_bits)]

    return {
        pattern[1:-1]: value
        for pattern, value in zip(pattern_bits, url_bits)
        if pattern != value
    }


def separate_params(params: List[dict]) -> Tuple[List, List[str]]:
    """Separate parameters explicitly defined and referenced by `$ref`"""
    reference_params = []
    regular_params = []
    for param in params:
        if param.get("$ref") is None:
            regular_params.append(param)
        else:
            reference_params.append(param)

    return regular_params, reference_params


def filter_header_regular_params(params: list) -> list:
    return [
        param for param in params if param["in"] == "header" and param.get("required")
    ]


def filter_header_reference_params(params: list, spec: dict) -> list:
    """Filter header parameters which are in definitions referenced with `$ref`"""
    header_params = []

    for param in params:
        reference = param.get("$ref")
        # Local reference case (parameter in specification document)
        if reference[:2] == "#/":
            split_path = reference[2:].split("/")
            tmp_parameter = spec
            for parent in split_path:
                tmp_parameter = tmp_parameter.get(parent)

            if tmp_parameter["in"] == "header" and tmp_parameter.get("required"):
                header_params.append(tmp_parameter)
        # TODO Remote reference case (parameter in a document on the same server)
        elif "//" not in reference:
            raise NotImplementedError("To be implemented")
        # TODO URL reference case (parameter in a document on another server)
        elif "//" in reference:
            raise NotImplementedError("To be implemented")

    return header_params


def filter_header_params(params: list, spec: dict) -> list:
    """Extract parameters required for headers"""
    # Separate the parameters that use references
    regular_parameters, reference_parameters = separate_params(params)

    # Filter regular and reference parameters
    header_regular_parameters = filter_header_regular_params(regular_parameters)
    header_reference_parameters = filter_header_reference_params(
        reference_parameters, spec
    )
    return header_regular_parameters + header_reference_parameters


def get_headers(spec: dict, operation: str) -> dict:
    """
    Extract required headers and use the default value from the API spec.
    """
    headers = {}

    for path, methods in spec["paths"].items():
        path_parameters = filter_header_params(methods.get("parameters", []), spec)
        for name, method in methods.items():
            if name == "parameters":
                continue

            if method["operationId"] != operation:
                continue

            method_parameters = filter_header_params(method.get("parameters", []), spec)

            for param in path_parameters + method_parameters:
                enum = param["schema"].get("enum", [])
                default = param["schema"].get("default")

                assert (
                    len(enum) == 1 or default
                ), "Can't choose an appropriate default header value"
                headers[param["name"]] = default or enum[0]

    return headers
