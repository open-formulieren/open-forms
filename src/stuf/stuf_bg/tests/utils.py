from unittest.mock import patch

from django.template import loader

from stuf.xml import fromstring


def mock_stufbg_client(template: str):
    return_value = get_mock_response_content(template, encode=False)
    patcher = patch(
        "stuf.stuf_bg.client.Client.get_values_for_attributes",
        return_value=return_value,
    )
    patcher.start()
    return patcher


def get_mock_response_content(template: str, encode: bool = True):
    xml_text = loader.render_to_string(f"stuf_bg/tests/responses/{template}")
    if encode:
        return xml_text.encode("utf-8")
    return xml_text


def get_mock_xml(template: str):
    return fromstring(get_mock_response_content(template))
