"""
XML parsing with DTD/Entities blocking.

Inspired by https://github.com/mvantellingen/python-zeep/pull/1179/ as their solution
for the deprecated defusedxml.lxml module and the defaults applied in defusedxml.lxml.
"""

import re
from typing import Any

from lxml.etree import XMLParser, fromstring as _fromstring

from openforms.utils.helpers import recursively_apply_function

# See invalid XML characters: https://www.w3.org/TR/xml/#charsets
INVALID_XML_CHARS = re.compile(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]")


def fromstring(content: str | bytes):
    """
    Create an LXML etree from the string content without resolving entities.

    Resolving entities is a security risk, which is why we disable it.
    """
    parser = XMLParser(resolve_entities=False)
    return _fromstring(content, parser=parser)


def strip_invalid_xml_chars(value: str) -> str:
    """
    Remove characters from a string that are not allowed in XML.

    This ensures that any string can safely be included in an XML document without
    causing parsing errors.
    """
    return INVALID_XML_CHARS.sub("", value)


def sanitize_users_input_data(full_context: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize keys that actually come from user input (initiator and extra).
    """
    if initiator_context := full_context.get("initiator"):
        full_context["initiator"] = recursively_apply_function(
            initiator_context, strip_invalid_xml_chars
        )
    if extra_context := full_context.get("extra"):
        # StUF-BG gives a plain dict
        if isinstance(extra_context, dict):
            full_context["extra"] = recursively_apply_function(
                extra_context, strip_invalid_xml_chars
            )
        # StUF-ZDS gives a LangInjection object (which holds the extra_data for the
        # extraElementen)
        else:
            extra_context.extra_data = recursively_apply_function(
                extra_context.extra_data, strip_invalid_xml_chars
            )

    return full_context
