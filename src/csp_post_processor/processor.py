import hashlib
import logging

from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

import bleach
import html5lib
import lxml.html
import tinycss2
from bleach import css_sanitizer
from lxml import etree
from rest_framework.request import Request

from .constants import NONCE_HTTP_HEADER

logger = logging.getLogger(__name__)

wysiwyg_allowed_protocols = ["http", "https", "mailto", "data"]

wysiwyg_allowed_tags = [
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
]

_tags_with_style = [
    # these will have _style_attrs added to the allowed tag/attr map below
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
_style_attrs = [
    "id",
    "class",
    "style",
]

wysiwyg_tag_allowed_attribute_map = {
    "a": ["href", "title", "rel", "target"],
    "abbr": ["title"],
    "acronym": ["title"],
    "img": ["width", "height", "alt", "src"],
    "figure": ["title", "src"],
    # CKEditor has a table designer with spans
    "td": ["colspan", "rowspan"],
    # Button class for NL DS styling + type
    "button": ["class", "type"],
}

wysiwyg_css_properties = list(css_sanitizer.ALLOWED_CSS_PROPERTIES)
wysiwyg_css_properties += [
    # TinyMCE uses padding-left for indent
    "padding-left",
    # TinyMCE uses list-style-type for list styling
    "list-style-type",
]

wysiwyg_svg_properties = list(css_sanitizer.ALLOWED_SVG_PROPERTIES)


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
        logger.info("No nonce available on the request, returning html unmodified.")
        return html

    lxml_etree_document = html5lib.parse(
        html,
        treebuilder="lxml",
        namespaceHTMLElements=False,
    )
    inline_styles = dict()

    for node in lxml_etree_document.iter():
        # scan for inline styles
        if not (style := node.attrib.get("style")):
            continue

        # remove the inline styles
        del node.attrib["style"]

        parsed_styles = tinycss2.parse_declaration_list(style)

        # apply CSS whitelist here because the bleach step won't see these styles after we extracted them
        parsed_styles = [
            s
            for s in parsed_styles
            if getattr(s, "lower_name", None) in wysiwyg_css_properties
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

    # did we extract style we want to keep?
    if inline_styles:
        style_element = etree.Element("style")
        style_element.attrib["nonce"] = csp_nonce

        # build the CSS from the inline styles
        all_styles = ""
        for unique_id, style in inline_styles.items():
            all_styles += f"#{unique_id} {{\n    {style}\n}} \n"

        style_element.text = f"\n{all_styles}\n"

        # convert styles to html string
        style_markup = lxml.html.tostring(
            style_element, encoding="unicode", pretty_print=True
        )
        style_markup = f"{style_markup}\n"
    else:
        style_markup = ""

    # convert back to a string
    root = lxml_etree_document.getroot()
    body = root.find("body")  # parsers wrap snippet in <html><body>...</body></html>
    parts = body.getchildren()
    if not parts:  # no nested HTML/elements
        return body.text or ""

    modified_html = "".join(
        [
            lxml.html.tostring(part, encoding="unicode", pretty_print=True)
            for part in parts
        ]
    )
    # run bleach on non-style part
    modified_html = bleach_wysiwyg_content(modified_html)

    result = SafeStringWrapper(mark_safe(f"{style_markup}{modified_html}"))

    # mark result as processed to avoid multiple calls
    result._csp_post_processed = True  # type: ignore

    return result


def bleach_wysiwyg_content(html):
    bleached = bleach.clean(
        html,
        tags=wysiwyg_allowed_tags,
        attributes=wysiwyg_tag_allowed_attribute_map,
        protocols=wysiwyg_allowed_protocols,
        # let's not strip tags to keep problems visible
        strip=False,
        strip_comments=True,
        css_sanitizer=css_sanitizer.CSSSanitizer(
            allowed_css_properties=wysiwyg_css_properties,
            allowed_svg_properties=wysiwyg_svg_properties,
        ),
    )
    return mark_safe(bleached)


def _add_wysiwyg_style_attributes_and_tags():
    # util to limit amount of manual edited data in the allowed_attribute_map
    for tag in _tags_with_style:
        # check if we forgot to add it to allowed tags
        if tag not in wysiwyg_allowed_tags:
            raise ValueError(
                f"adding tag '{tag}' to tag_attr_map but missing from 'allowed_tags'"
            )

        # add style attrs to tag/attr map
        if tag in wysiwyg_tag_allowed_attribute_map:
            for attr in _style_attrs:
                if attr not in wysiwyg_tag_allowed_attribute_map[tag]:
                    wysiwyg_tag_allowed_attribute_map[tag].append(attr)
        else:
            wysiwyg_tag_allowed_attribute_map[tag] = _style_attrs.copy()

    # check if tags in attr map exist in allowed tags
    for tag in wysiwyg_tag_allowed_attribute_map.keys():
        if tag not in wysiwyg_allowed_tags:
            raise ValueError(
                f"adding tag '{tag}' to tag_attr_map but missing from 'allowed_tags'"
            )


_add_wysiwyg_style_attributes_and_tags()
