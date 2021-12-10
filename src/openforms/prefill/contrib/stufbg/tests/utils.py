from unittest.mock import patch

from django.template import loader

from ....registry import register

plugin = register["stufbg"]


def mock_stufbg_client(template: str):
    patcher = patch("openforms.prefill.contrib.stufbg.plugin.StufBGConfig.get_solo")
    mock_client = patcher.start()
    get_values_for_attributes_mock = (
        mock_client.return_value.get_client.return_value.get_values_for_attributes
    )
    get_values_for_attributes_mock.return_value = loader.render_to_string(
        f"stuf_bg/tests/responses/{template}"
    )
    return patcher
