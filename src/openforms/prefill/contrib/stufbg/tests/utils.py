from unittest.mock import patch

from django.template import loader

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
