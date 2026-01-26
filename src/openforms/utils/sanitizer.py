from django.core.files import File

import nh3

ALLOWED_SVG_TAGS: set[str] = {
    "circle",
    "clipPath",
    "defs",
    "desc",
    "ellipse",
    "feBlend",
    "feColorMatrix",
    "feComponentTransfer",
    "feComposite",
    "feConvolveMatrix",
    "feDiffuseLighting",
    "feDisplacementMap",
    "feDistantLight",
    "feDropShadow",
    "feFlood",
    "feFuncA",
    "feFuncB",
    "feFuncG",
    "feFuncR",
    "feGaussianBlur",
    "feImage",
    "feMerge",
    "feMergeNode",
    "feMorphology",
    "feOffset",
    "fePointLight",
    "feSpecularLighting",
    "feSpotLight",
    "feTile",
    "feTurbulence",
    "filter",
    "foreignObject",
    "g",
    "image",
    "line",
    "linearGradient",
    "marker",
    "mask",
    "metadata",
    "mpath",
    "path",
    "pattern",
    "polygon",
    "polyline",
    "radialGradient",
    "rect",
    "set",
    "stop",
    "style",
    "svg",
    "symbol",
    "text",
    "textPath",
    "title",
    "tspan",
    "use",
    "view",
    # --- Not allowing 'a', 'animate*' and 'script' tags
}

ALLOWED_SVG_ATTRIBUTES: dict[str, set[str]] = {
    "*": {
        # --- Basic presentation attributes
        "alignment-baseline",
        "baseline-shift",
        "clip",
        "clip-path",
        "clip-rule",
        "color",
        "color-interpolation",
        "color-interpolation-filters",
        "cursor",
        "cx",
        "cy",
        "d",
        "direction",
        "display",
        "dominant-baseline",
        "fill",
        "fill-opacity",
        "fill-rule",
        "filter",
        "flood-color",
        "flood-opacity",
        "font-family",
        "font-size",
        "font-size-adjust",
        "font-stretch",
        "font-style",
        "font-variant",
        "font-weight",
        "glyph-orientation-horizontal",
        "glyph-orientation-vertical",
        "height",
        "image-rendering",
        "letter-spacing",
        "lighting-color",
        "marker-end",
        "marker-mid",
        "marker-start",
        "mask",
        "mask-type",
        "opacity",
        "overflow",
        "pointer-events",
        "r",
        "rx",
        "ry",
        "shape-rendering",
        "stop-color",
        "stop-opacity",
        "stroke",
        "stroke-dasharray",
        "stroke-dashoffset",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-miterlimit",
        "stroke-opacity",
        "stroke-width",
        "text-anchor",
        "text-decoration",
        "text-overflow",
        "text-rendering",
        "transform",
        "transform-origin",
        "unicode-bidi",
        "vector-effect",
        "visibility",
        "white-space",
        "width",
        "word-spacing",
        "writing-mode",
        "x",
        "y",
        # --- Filter attributes
        "amplitude",
        "exponent",
        "intercept",
        "offset",
        "slope",
        "tableValues",
        "type",
        # --- Not allowing 'href', 'data-*', Animation and some other attributes
    },
    "svg": {"xmlns", "viewBox"},
}

ALLOWED_HTML_TAGS: set[str] = {
    # Basic text tags
    "a",
    "b",
    "br",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "i",
    "p",
    "s",
    "strong",
    "sup",
    "u",
    # Lists
    "li",
    "ol",
    "ul",
}

ALLOWED_HTML_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "target", "rel", "data-fr-linked"},
}

ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto"}


def sanitize_svg_file(data: File) -> File:
    """
    Defuse an uploaded SVG file.

    The entire file content will be replaced with a sanitized version. All tags and
    attributes that aren't explicitly allowed, are removed from the SVG content.

    :arg data: the uploaded SVG file, opened in binary mode.
    """
    # Making sure that the file is reset properly
    data.seek(0)

    file_content = data.read().decode("utf-8")
    sanitized_content = sanitize_svg_content(file_content)

    # Replace svg file content with the cleaned variant.
    # `truncate(0)` doesn't reset the point, so start with a seek(0) to make sure the
    # content is as expected.
    data.seek(0)
    data.truncate(0)
    data.write(sanitized_content.encode("utf-8"))

    # Reset pointer
    data.seek(0)
    return data


def sanitize_svg_content(svg_content: str) -> str:
    """
    Strip (potentially) dangerous elements and attributes from the provided SVG string.

    All tags and attributes that aren't explicitly allowed, are removed from the SVG
    content.

    :arg svg_content: decoded SVG content.

    .. warning:: Do not use in security-critical contexts - using nh3 or bleach for
       SVG content sanitizing is best-effort and not what it's made for.

    .. danger:: Do not inline the result of this function in HTML!
    """

    return nh3.clean(
        svg_content,
        tags=ALLOWED_SVG_TAGS,
        # default: https://github.com/rust-ammonia/ammonia/blob/a0ebe263665931a16ff42c48b446465c52e8a78c/src/lib.rs#L389
        clean_content_tags={"script"},
        attributes=ALLOWED_SVG_ATTRIBUTES,
        strip_comments=True,
        url_schemes=ALLOWED_URL_SCHEMES,
    )


def sanitize_html_content(html_content: str) -> str:
    """
    Defuse html string.

    The provided string is replaced by a html sanitized version. All tags and attributes
    that aren't explicitly allowed, are removed from the SVG content.

    :arg html_content: the html string to sanitize.
    """
    return nh3.clean(
        html_content,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip_comments=True,
        link_rel=None,
        url_schemes=ALLOWED_URL_SCHEMES,
    )
