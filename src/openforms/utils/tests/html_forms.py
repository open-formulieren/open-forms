from typing import Literal

from bs4 import BeautifulSoup

type Method = Literal["get", "post"]


def parse_form(html_content: str | bytes) -> tuple[Method, str, dict[str, str]]:
    """
    Extract method, action URL and form values from html content.

    Inspired by Webtest's Form class.

    Not all input types are currently supported - only what's actually used in existing
    tests.
    """
    html = BeautifulSoup(html_content, "html.parser")
    attrs = html("form")[0].attrs
    action = attrs.get("action", "")
    assert isinstance(action, str)
    _method = attrs.get("method", "get")
    assert isinstance(_method, str)
    assert _method in ("get", "post")
    method: Method = _method

    # parse the fields
    tags = ("input", "select", "textarea")
    elements = html.find_all(tags)

    submit_fields: dict[str, str] = {}
    for node in elements:
        attrs = node.attrs
        tag = node.name
        name = attrs.pop("name", None)
        assert isinstance(name, str | None)
        if name is None:
            continue

        value: str
        match tag:
            case "input":
                _input_type = attrs.get("type", "text")
                assert isinstance(_input_type, str)
                input_type: str = _input_type.lower()
                match input_type:
                    case "checkbox" | "file":
                        raise NotImplementedError
                    case "radio" if "checked" in attrs and "value" in attrs:
                        _value = attrs["value"]
                        assert isinstance(_value, str)
                        submit_fields[name] = _value
                    case _:
                        _value = attrs.get("value", "")
                        assert isinstance(_value, str)
                        submit_fields[name] = _value

            case "select":
                if "multiple" in attrs:
                    raise NotImplementedError

                value = ""
                for option in node("option"):
                    selected = "selected" in option.attrs
                    if selected:
                        _value = option.attrs.get("value", "")
                        assert isinstance(_value, str)
                        value = _value

                submit_fields[name] = value

            case "textarea":
                value = node.text.lstrip()
                submit_fields[name] = value

            case _:  # pragma: no cover
                raise AssertionError(f"Unhandled tag type: {tag}")

    return method, action, submit_fields
