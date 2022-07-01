from djchoices import ChoiceItem, DjangoChoices


class CSPDirective(DjangoChoices):
    # via https://django-csp.readthedocs.io/en/latest/configuration.html
    DEFAULT_SRC = ChoiceItem("default-src", label="default-src")
    SCRIPT_SRC = ChoiceItem("script-src", label="script-src")
    SCRIPT_SRC_ATTR = ChoiceItem("script-src-attr", label="script-src-attr")
    SCRIPT_SRC_ELEM = ChoiceItem("script-src-elem", label="script-src-elem")
    IMG_SRC = ChoiceItem("img-src", label="img-src")
    OBJECT_SRC = ChoiceItem("object-src", label="object-src")
    PREFETCH_SRC = ChoiceItem("prefetch-src", label="prefetch-src")
    MEDIA_SRC = ChoiceItem("media-src", label="media-src")
    FRAME_SRC = ChoiceItem("frame-src", label="frame-src")
    FONT_SRC = ChoiceItem("font-src", label="font-src")
    CONNECT_SRC = ChoiceItem("connect-src", label="connect-src")
    STYLE_SRC = ChoiceItem("style-src", label="style-src")
    STYLE_SRC_ATTR = ChoiceItem("style-src-attr", label="style-src-attr")
    STYLE_SRC_ELEM = ChoiceItem("style-src-elem", label="style-src-elem")
    BASE_URI = ChoiceItem(
        "base-uri", label="base-uri"
    )  # Note: This doesn’t use default-src as a fall-back.
    CHILD_SRC = ChoiceItem(
        "child-src", label="child-src"
    )  # Note: Deprecated in CSP v3. Use frame-src and worker-src instead.
    FRAME_ANCESTORS = ChoiceItem(
        "frame-ancestors", label="frame-ancestors"
    )  # Note: This doesn’t use default-src as a fall-back.
    NAVIGATE_TO = ChoiceItem(
        "navigate-to", label="navigate-to"
    )  # Note: This doesn’t use default-src as a fall-back.
    FORM_ACTION = ChoiceItem(
        "form-action", label="form-action"
    )  # Note: This doesn’t use default-src as a fall-back.
    SANDBOX = ChoiceItem(
        "sandbox", label="sandbox"
    )  # Note: This doesn’t use default-src as a fall-back.
    REPORT_URI = ChoiceItem(
        "report-uri", label="report-uri"
    )  # Each URI can be a full or relative URI. None Note: This doesn’t use default-src as a fall-back.
    REPORT_TO = ChoiceItem(
        "report-to", label="report-to"
    )  # A string describing a reporting group. None Note: This doesn’t use default-src as a fall-back. See Section 1.2: https://w3c.github.io/reporting/#group
    MANIFEST_SRC = ChoiceItem("manifest-src", label="manifest-src")
    WORKER_SRC = ChoiceItem("worker-src", label="worker-src")
    PLUGIN_TYPES = ChoiceItem(
        "plugin-types", label="plugin-types"
    )  # Note: This doesn’t use default-src as a fall-back.
    REQUIRE_SRI_FOR = ChoiceItem(
        "require-sri-for", label="require-sri-for"
    )  # Valid values: script, style, or both. See: require-sri-for-known-tokens Note: This doesn’t use default-src as a fall-back.

    # CSP_UPGRADE_INSECURE_REQUESTS  # Include upgrade-insecure-requests directive. A boolean. False See: upgrade-insecure-requests
    # CSP_BLOCK_ALL_MIXED_CONTENT  # Include block-all-mixed-content directive. A boolean. False See: block-all-mixed-content
    # CSP_INCLUDE_NONCE_IN  # Include dynamically generated nonce in all listed directives, e.g. CSP_INCLUDE_NONCE_IN=['script-src'] will add 'nonce-<b64-value>' to the script-src directive.
