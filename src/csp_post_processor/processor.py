import hashlib

from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

import lxml.html
import nh3
import structlog
import tinycss2
from lxml import etree
from rest_framework.request import Request

from .constants import NONCE_HTTP_HEADER

logger = structlog.stdlib.get_logger(__name__)

WYSIWYG_ALLOWED_PROTOCOLS: set[str] = {"http", "https", "mailto", "data"}

WYSIWYG_ALLOWED_TAGS: set[str] = {
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    # -- added
    "br",
    "p",
    "img",
    "figure",
    "figcaption",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "span",
    "div",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
    "button",
    # NOTE we don't add "style" here
}

_TAGS_WITH_STYLE = [
    # these will have _STYLE_ATTRS added to the allowed tag/attr map below
    "a",
    "p",
    "figure",
    "img",
    "div",
    "span",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
]
_STYLE_ATTRS: set[str] = {
    "id",
    "class",
    "style",
}

WYSIWYG_TAG_ALLOWED_ATTRIBUTE_MAP: dict[str, set[str]] = {
    "a": {"href", "title", "rel", "target"},
    "abbr": {"title"},
    "acronym": {"title"},
    "img": {"width", "height", "alt", "src"},
    "figure": {"title", "src"},
    # CKEditor has a table designer with spans
    "td": {"colspan", "rowspan"},
    # Button class for NL DS styling + type
    "button": {"class", "type"},
}

# set taken from bleach
WYSIWYG_CSS_PROPERTIES: set[str] = {
    "azimuth",
    "background-color",
    "border-bottom-color",
    "border-collapse",
    "border-color",
    "border-left-color",
    "border-right-color",
    "border-top-color",
    "clear",
    "color",
    "cursor",
    "direction",
    "display",
    "elevation",
    "float",
    "font",
    "font-family",
    "font-size",
    "font-style",
    "font-variant",
    "font-weight",
    "height",
    "letter-spacing",
    "line-height",
    "overflow",
    "pause",
    "pause-after",
    "pause-before",
    "pitch",
    "pitch-range",
    "richness",
    "speak",
    "speak-header",
    "speak-numeral",
    "speak-punctuation",
    "speech-rate",
    "stress",
    "text-align",
    "text-decoration",
    "text-indent",
    "unicode-bidi",
    "vertical-align",
    "voice-family",
    "volume",
    "white-space",
    "width",
    # extended with our own needs
} | {
    # TinyMCE uses list-style-type for list styling
    "list-style-type",
    # TinyMCE uses padding-left for indent
    "padding-left",
}
WYSIWYG_SVG_PROPERTIES: set[str] = {
    "fill",
    "fill-opacity",
    "fill-rule",
    "stroke",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-opacity",
    "stroke-width",
}


class SafeStringWrapper(SafeString):
    # Django 4.2 added slots to the SafeString class (https://docs.djangoproject.com/en/4.2/_modules/django/utils/safestring/#SafeString)
    # So we cannot set the _csp_post_processed attribute. This wrapper is a workaround
    _csp_post_processed = False


def get_html_id(node):
    return str(id(node))  # CPython: memory address, so should be unique enough


def post_process_html(
    html: str | SafeStringWrapper, request: HttpRequest | Request
) -> str:
    """
    Replacing inline style attributes with an inline <style> element with nonce added.

    Inline style attributes cannot have a nonce, but the elements can get an ID and be
    targetted via an inline <style> element in the markup which _can_ have a nonce.

    The nonce is taken from the request object, typically set by the django-csp
    middleware.

    If an HTML id is generated, we prefix it with the nonce value to prevent collisions
    with possible other IDs.
    """
    if getattr(html, "_csp_post_processed", False):
        return html

    if not (csp_nonce := request.headers.get(NONCE_HTTP_HEADER)):
        logger.info("skip_processing", reason="nonce_not_found")
        return html

    # mimick html5lib wrapping content in <html><body>...</body></html>
    lxml_etree_document = lxml.html.fromstring(f"<html><body>{html}</body></html>")
    inline_styles: dict[str, str] = {}

    for node in lxml_etree_document.iter():
        # scan for inline styles
        if not (style := node.attrib.get("style")):
            continue

        # remove the inline styles
        del node.attrib["style"]

        parsed_styles = tinycss2.parse_declaration_list(style)

        # apply CSS allowlist here because the cleaning step won't see these styles after
        # we extracted them
        parsed_styles = [
            s
            for s in parsed_styles
            if getattr(s, "lower_name", None) in WYSIWYG_CSS_PROPERTIES
        ]
        if not parsed_styles:
            continue

        # generate an ID if we don't have one
        if not (html_id := node.attrib.get("id")):
            html_id = get_html_id(node)
            # csp_nonce is b64 encoded and can contain chars that are not allowed for
            # HTML IDs -> md5 hash it
            hashed_nonce = hashlib.md5(csp_nonce.encode("ascii")).hexdigest()
            html_id = f"nonce-{hashed_nonce}-{html_id}"
            # set the generated ID which is referenced in the inline styles
            node.attrib["id"] = html_id

        # keep the ID and CSS
        inline_styles[html_id] = tinycss2.serialize(parsed_styles)

    # convert back to a string
    root = lxml_etree_document
    body = root.find("body")
    assert body is not None
    parts = list(body)
    if not parts:  # no nested HTML/elements
        return body.text or ""

    modified_html = "".join(
        [
            lxml.html.tostring(part, encoding="unicode", pretty_print=True)
            for part in parts
        ]
    )
    # sanitize the non-style part
    modified_html = sanitize_wysiwyg_content(modified_html)

    # did we extract style we want to keep?
    style_markup: str = ""
    if inline_styles:
        style_element = etree.Element("style")
        style_element.attrib["nonce"] = csp_nonce

        # build the CSS from the inline styles
        all_styles = ""
        for unique_id, style in inline_styles.items():
            if f'id="{unique_id}"' not in modified_html:
                continue
            all_styles += f"#{unique_id} {{\n    {style}\n}} \n"

        if all_styles:
            style_element.text = f"\n{all_styles}\n"
            # convert styles to html string
            style_markup = lxml.html.tostring(
                style_element, encoding="unicode", pretty_print=True
            )
            style_markup = f"{style_markup}\n"

    result = SafeStringWrapper(mark_safe(f"{style_markup}{modified_html}"))

    # mark result as processed to avoid multiple calls
    result._csp_post_processed = True  # type: ignore

    return result


def sanitize_wysiwyg_content(html):
    cleaned = nh3.clean(
        html,
        tags=WYSIWYG_ALLOWED_TAGS,
        attributes=WYSIWYG_TAG_ALLOWED_ATTRIBUTE_MAP,
        url_schemes=WYSIWYG_ALLOWED_PROTOCOLS,
        link_rel=None,
        strip_comments=True,
        filter_style_properties=WYSIWYG_CSS_PROPERTIES | WYSIWYG_SVG_PROPERTIES,
    )
    return mark_safe(cleaned)


def _add_wysiwyg_style_attributes_and_tags():
    # util to limit amount of manual edited data in the allowed_attribute_map
    for tag in _TAGS_WITH_STYLE:
        # check if we forgot to add it to allowed tags
        if tag not in WYSIWYG_ALLOWED_TAGS:  # pragma: no cover
            raise ValueError(
                f"adding tag '{tag}' to tag_attr_map but missing from 'allowed_tags'"
            )

        # add style attrs to tag/attr map
        if tag in WYSIWYG_TAG_ALLOWED_ATTRIBUTE_MAP:
            for attr in _STYLE_ATTRS:
                if attr not in WYSIWYG_TAG_ALLOWED_ATTRIBUTE_MAP[tag]:
                    WYSIWYG_TAG_ALLOWED_ATTRIBUTE_MAP[tag].add(attr)
        else:
            WYSIWYG_TAG_ALLOWED_ATTRIBUTE_MAP[tag] = _STYLE_ATTRS.copy()

    # check if tags in attr map exist in allowed tags
    for tag in WYSIWYG_TAG_ALLOWED_ATTRIBUTE_MAP.keys():
        if tag not in WYSIWYG_ALLOWED_TAGS:  # pragma: no cover
            raise ValueError(
                f"adding tag '{tag}' to tag_attr_map but missing from 'allowed_tags'"
            )


_add_wysiwyg_style_attributes_and_tags()
