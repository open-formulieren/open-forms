from contextlib import contextmanager, nullcontext
from pathlib import Path
from unittest.mock import patch

from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

TEST_FILES = Path(__file__).parent.resolve() / "data"


@contextmanager
def mock_saml2_return_flow(
    mock_saml_art_verification: bool = False,
    verify_error: OneLogin_Saml2_ValidationError | None = None,
    get_attributes_error: OneLogin_Saml2_ValidationError | None = None,
):
    """
    Apply mocks in various stages of the SAMLv2 flow.

    Our SAMLv2 client performs some checks via the python3-saml library and additional
    extra security checks via django-digid-eherkenning. The nature of these checks is
    non-deterministic: random ID generation, IP addresses, timestamps.

    This mock helper pins certain aspects or bypasses checks entirely for the sake of
    being able to test our client usage.
    """
    mock_xml_validation = patch(
        "onelogin.saml2.xml_utils.OneLogin_Saml2_XML.validate_xml", return_value=True
    )
    mock_unique_id = patch(
        "onelogin.saml2.utils.OneLogin_Saml2_Utils.generate_unique_id",
        return_value="_1330416516",
    )
    mock_response_validation = (
        patch(
            "onelogin.saml2.response.OneLogin_Saml2_Response.is_valid",
            return_value=True,
        )
        if mock_saml_art_verification
        else nullcontext()
    )
    mock_saml_response_validation = (
        patch(
            "digid_eherkenning.saml2.base.BaseSaml2Client.verify_saml2_response",
            return_value=True,
            side_effect=verify_error,
        )
        if (mock_saml_art_verification or verify_error)
        else nullcontext()
    )
    mock_get_attributes = (
        patch(
            "onelogin.saml2.response.OneLogin_Saml2_Response.get_attributes",
            side_effect=get_attributes_error,
        )
        if get_attributes_error
        else nullcontext()
    )

    with (
        mock_xml_validation,
        mock_unique_id,
        mock_response_validation,
        mock_saml_response_validation,
        mock_get_attributes,
    ):
        yield
