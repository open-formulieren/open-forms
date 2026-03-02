"""
XML parsing with DTD/Entities blocking.

Inspired by https://github.com/mvantellingen/python-zeep/pull/1179/ as their solution
for the deprecated defusedxml.lxml module and the defaults applied in defusedxml.lxml.
"""

import re
from typing import Any

from lxml.etree import XMLParser, fromstring as _fromstring

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
    if not isinstance(value, str):
        return value
    return INVALID_XML_CHARS.sub("", value)


def sanitize_dict_for_xml(dict_input: dict) -> dict:
    """
    Recursively sanitize all string values in a dictionary for XML.

    This function traverses the dictionary, removing illegal XML characters from any
    string values. Nested dictionaries are sanitized recursively, while non-string
    values are left unchanged.
    """
    assert isinstance(dict_input, dict)

    sanitized = {}
    for k, v in dict_input.items():
        if isinstance(v, str):
            sanitized[k] = strip_invalid_xml_chars(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict_for_xml(v)
        else:
            sanitized[k] = v
    return sanitized


def sanitize_users_data(full_context: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize keys that actually come from user input (initiator and extra).
    """
    if initiator_context := full_context.get("initiator"):
        full_context["initiator"] = sanitize_dict_for_xml(initiator_context)
    if extra_context := full_context.get("extra"):
        # StUF-BG gives a plain dict
        # StUF-ZDS gives a LangInjection object (which holds the extra_data for the
        # extraElementen)
        if isinstance(extra_context, dict):
            for k, v in full_context["extra"].items():
                if isinstance(v, str):
                    full_context["extra"][k] = strip_invalid_xml_chars(v)
        else:
            lang_injection_obj = extra_context
            for k, v in lang_injection_obj.extra_data.items():
                if isinstance(v, str):
                    lang_injection_obj.extra_data[k] = strip_invalid_xml_chars(v)

    return full_context
