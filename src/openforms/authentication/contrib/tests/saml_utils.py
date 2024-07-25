from base64 import b64encode
from hashlib import sha1
from pathlib import Path

from digid_eherkenning.models import EherkenningConfiguration
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from openforms.template import render_from_string


def create_test_artifact(service_entity_id: str = "") -> str:
    type_code = b"\x00\x04"
    endpoint_index = b"\x00\x00"
    sha_entity_id = sha1(service_entity_id.encode("utf-8")).digest()
    message_handle = b"01234567890123456789"  # something random
    b64encoded = b64encode(type_code + endpoint_index + sha_entity_id + message_handle)
    return b64encoded.decode("ascii")


def get_artifact_response(filepath: str, context: dict | None = None) -> bytes:
    template_source = Path(filepath).read_text()
    return render_from_string(template_source, context or {}).encode("utf-8")


def get_encrypted_attribute(attr: str, identifier: str):
    config = EherkenningConfiguration.get_solo()
    certificate, _ = config.select_certificates()
    with certificate.public_certificate.open("r") as cert_file:
        cert = cert_file.read()
    return OneLogin_Saml2_Utils.generate_name_id(
        identifier,
        sp_nq=None,
        nq=f"urn:etoegang:1.9:EntityConcernedID:{attr}",
        sp_format="urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
        cert=cert,
    )
