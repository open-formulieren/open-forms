from unittest.mock import patch

from django.template import loader

from defusedxml.lxml import fromstring as df_fromstring

from ....registry import register

plugin = register["stufbg"]


def mock_stufbg_client(template: str):
    return_value = loader.render_to_string(f"stuf_bg/tests/responses/{template}")
    patcher = patch(
        "stuf.stuf_bg.client.StufBGClient.get_values_for_attributes",
        return_value=return_value,
    )
    patcher.start()
    return patcher


def mock_stufbg_make_request(template: str):
    return_value = loader.render_to_string(f"stuf_bg/tests/responses/{template}")

    class FakeResponse:
        content = return_value.encode("utf")

        def raise_for_status(self):
            pass

    patcher = patch(
        "stuf.stuf_bg.client.StufBGClient.make_request",
        return_value=FakeResponse(),
    )
    patcher.start()
    return patcher


def get_mock_xml(template: str):
    xml_text = loader.render_to_string(f"stuf_bg/tests/responses/{template}")
    xml = df_fromstring(xml_text.encode("utf8"))
    return xml
