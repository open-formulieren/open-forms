from django.db import models
from django.utils.translation import gettext_lazy as _


class CSPDirective(models.TextChoices):
    # via https://django-csp.readthedocs.io/en/latest/configuration.html
    DEFAULT_SRC = "default-src", "default-src"
    SCRIPT_SRC = "script-src", "script-src"
    SCRIPT_SRC_ATTR = "script-src-attr", "script-src-attr"
    SCRIPT_SRC_ELEM = "script-src-elem", "script-src-elem"
    IMG_SRC = "img-src", "img-src"
    OBJECT_SRC = "object-src", "object-src"
    PREFETCH_SRC = "prefetch-src", "prefetch-src"
    MEDIA_SRC = "media-src", "media-src"
    FRAME_SRC = "frame-src", "frame-src"
    FONT_SRC = "font-src", "font-src"
    CONNECT_SRC = "connect-src", "connect-src"
    STYLE_SRC = "style-src", "style-src"
    STYLE_SRC_ATTR = "style-src-attr", "style-src-attr"
    STYLE_SRC_ELEM = "style-src-elem", "style-src-elem"
    BASE_URI = (
        "base-uri",
        "base-uri",
    )  # Note: This doesn’t use default-src as a fall-back.
    CHILD_SRC = (
        "child-src",
        "child-src",
    )  # Note: Deprecated in CSP v3. Use frame-src and worker-src instead.
    FRAME_ANCESTORS = (
        "frame-ancestors",
        "frame-ancestors",
    )  # Note: This doesn’t use default-src as a fall-back.
    NAVIGATE_TO = (
        "navigate-to",
        "navigate-to",
    )  # Note: This doesn’t use default-src as a fall-back.
    FORM_ACTION = (
        "form-action",
        "form-action",
    )  # Note: This doesn’t use default-src as a fall-back.
    SANDBOX = "sandbox", "sandbox"  # Note: This doesn’t use default-src as a fall-back.
    REPORT_URI = (
        "report-uri",
        "report-uri",
    )  # Each URI can be a full or relative URI. None Note: This doesn’t use default-src as a fall-back.
    REPORT_TO = (
        "report-to",
        "report-to",
    )  # A string describing a reporting group. None Note: This doesn’t use default-src as a fall-back. See Section 1.2: https://w3c.github.io/reporting/#group
    MANIFEST_SRC = "manifest-src", "manifest-src"
    WORKER_SRC = "worker-src", "worker-src"
    PLUGIN_TYPES = (
        "plugin-types",
        "plugin-types",
    )  # Note: This doesn’t use default-src as a fall-back.
    REQUIRE_SRI_FOR = (
        "require-sri-for",
        "require-sri-for",
    )  # Valid values: script, style, or both. See: require-sri-for-known-tokens Note: This doesn’t use default-src as a fall-back.


class UploadFileType(models.TextChoices):
    all = "*", _("any filetype")
    heic = "image/heic", (".heic")
    png = "image/png", _(".png")
    jpg = "image/jpeg", _(".jpg")
    pdf = "application/pdf", _(".pdf")
    xls = "application/vnd.ms-excel", _(".xls")
    xlsx = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        _(".xlsx"),
    )
    csv = "text/csv", _(".csv")
    txt = "text/plain", (".txt")
    doc = "application/msword", _(".doc")
    docx = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        _(".docx"),
    )
    open_office = (
        "application/vnd.oasis.opendocument.*,application/vnd.stardivision.*,application/vnd.sun.xml.*",
        _("Open Office"),
    )
    zip = (
        "application/zip,application/zip-compressed,application/x-zip-compressed",
        _(".zip"),
    )
    rar = "application/vnd.rar", _(".rar")
    tar = "application/x-tar", _(".tar")
    msg = "application/vnd.ms-outlook", _(".msg")
    dwg = (
        "application/acad.dwg,application/autocad_dwg.dwg,application/dwg.dwg,application/x-acad.dwg,"
        "application/x-autocad.dwg,application/x-dwg.dwg,drawing/dwg.dwg,image/vnd.dwg,image/x-dwg.dwg",
        _(".dwg"),
    )


class FamilyMembersDataAPIChoices(models.TextChoices):
    haal_centraal = "haal_centraal", _("Haal Centraal")
    stuf_bg = "stuf_bg", _("StufBg")


DEFAULT_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
