"""
XML parsing with DTD/Entities blocking.

Inspired by https://github.com/mvantellingen/python-zeep/pull/1179/ as their solution
for the deprecated defusedxml.lxml module and the defaults applied in defusedxml.lxml.
"""

from lxml.etree import XMLParser, fromstring as _fromstring


def fromstring(content: str | bytes):
    """
    Create an LXML etree from the string content without resolving entities.

    Resolving entities is a security risk, which is why we disable it.
    """
    parser = XMLParser(resolve_entities=False)
    return _fromstring(content, parser=parser)
