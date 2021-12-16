from base64 import b64encode
from hashlib import sha1
from typing import Optional

from django.conf import settings
from django.template import Context, Template

from onelogin.saml2.utils import OneLogin_Saml2_Utils


def create_test_artifact(service_entity_id: str = "") -> str:
    type_code = b"\x00\x04"
    endpoint_index = b"\x00\x00"
    sha_entity_id = sha1(service_entity_id.encode("utf-8")).digest()
    message_handle = b"01234567890123456789"  # something random
    b64encoded = b64encode(type_code + endpoint_index + sha_entity_id + message_handle)
    return b64encoded.decode("ascii")


def get_artifact_response(filepath: str, context: Optional[dict] = None) -> bytes:
    with open(filepath, "r") as template_source_file:
        template = Template(template_source_file.read())

    rendered = template.render(Context(context or {}))
    return rendered.encode("utf-8")


def get_encrypted_attribute(attr: str, identifier: str):
    with open(settings.EHERKENNING["cert_file"], "r") as cert_file:
        cert = cert_file.read()
    return OneLogin_Saml2_Utils.generate_name_id(
        identifier,
        sp_nq=None,
        nq=f"urn:etoegang:1.9:EntityConcernedID:{attr}",
        sp_format="urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
        cert=cert,
    )
