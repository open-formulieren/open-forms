import hashlib
import logging
from collections import defaultdict
from typing import List, Optional, Union

from django.http import HttpRequest

import html5lib
import lxml.html
import tinycss2
from lxml import etree
from rest_framework.request import Request

from .constants import NONCE_HTTP_HEADER

logger = logging.getLogger(__name__)


def get_html_id(node):
    return str(id(node))  # CPython: memory address, so should be unique enough


def post_process_html(
    html: str,
    request: Union[HttpRequest, Request],
    *,
    allowed_css_declarations: Optional[List[str]] = None,
) -> str:
    """
    Replacing inline style attributes with an inline <style> element with nonce added.

    Inline style attributes cannot have a nonce, but the elements can get an ID and be
    targetted via an inline <style> element in the markup which _can_ have a nonce.

    The nonce is taken from the request object, typically set by the django-csp
    middleware.

    If an HTML id is generated, we prefix it with the nonce value to prevent collisions
    with possible other IDs.

    The optional argument `allowed_css_declarations` specifies an allow-list of safe
    CSS declarations (for example: ["width", "font-color"]).
    """
    if not (csp_nonce := request.headers.get(NONCE_HTTP_HEADER)):
        logger.info("No nonce available on the request, returning html unmodified.")
        return html

    lxml_etree_document = html5lib.parse(
        html,
        treebuilder="lxml",
        namespaceHTMLElements=False,
    )
    inline_styles = defaultdict(list)

    for node in lxml_etree_document.iter():
        # scan for inline styles
        if not (style := node.attrib.get("style")):
            continue

        # remove the inline styles
        del node.attrib["style"]

        if not (html_id := node.attrib.get("id")):
            html_id = get_html_id(node)
            # csp_nonce is b64 encoded and can contain chars that are not allowed for
            # HTML IDs -> md5 hash it
            hashed_nonce = hashlib.md5(csp_nonce.encode("ascii")).hexdigest()
            html_id = f"nonce-{hashed_nonce}-{html_id}"
            # set the generated ID which is referenced in the inline styles
            node.attrib["id"] = html_id

        inline_styles[html_id] = style

    style_element = etree.Element("style")
    style_element.attrib["nonce"] = csp_nonce

    # build the CSS from the inline styles
    all_styles = ""
    for unique_id, style in inline_styles.items():
        parsed_styles = tinycss2.parse_declaration_list(style)
        if allowed_css_declarations is not None:
            parsed_styles = [
                s
                for s in parsed_styles
                if getattr(s, "lower_name", None) in allowed_css_declarations
            ]

        element_styles = tinycss2.serialize(parsed_styles)
        all_styles += f"#{unique_id} {{\n    {element_styles}\n}}"

    style_element.text = f"\n{all_styles}\n"

    # convert back to a string
    root = lxml_etree_document.getroot()
    style_markup = lxml.html.tostring(
        style_element, encoding="unicode", pretty_print=True
    )
    body = root.find("body")  # parsers wrap snippet in <html><body>...</body></html>
    parts = body.getchildren()
    if not parts:  # no nested HTML/elements
        return body.text

    modified_html = "".join(
        [
            lxml.html.tostring(part, encoding="unicode", pretty_print=True)
            for part in parts
        ]
    )
    return f"{style_markup}\n{modified_html}"
