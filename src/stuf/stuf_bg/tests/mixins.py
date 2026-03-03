from unittest.mock import patch

from ..mixins import StUFBGBaseMixin


class StUFBGAssertionsMixin(StUFBGBaseMixin):
    """Provides assertion/helper methods for StUF-BG XML testing."""

    def mock_stufbg_client(self, return_value: bytes):
        """
        Mock the client's response.
        """
        patcher = patch(
            "stuf.stuf_bg.client.Client.get_values_for_attributes",
            return_value=return_value,
        )
        patcher.start()
        return patcher

    def assertSoapBodyIsValid(self, xml_body: str | bytes) -> None:
        """
        Assert that a SOAP body XML complies with the XSD schema.

        The order of all elements in request doc does matter.
        """
        soap_body = self.extract_soap_body(xml_body)
        try:
            self.xml_schema.assert_(soap_body)
        except AssertionError as exc:
            self.fail(f"SOAP body is invalid: {exc}")
