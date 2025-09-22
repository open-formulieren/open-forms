from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.utils import timezone

from lxml.etree import XMLParser, fromstring as _fromstring

from openforms.utils.date import format_date_value

from .typing import StufBgIncompleteDateType

TIMEZONE_AMS = ZoneInfo("Europe/Amsterdam")


def normalize_date_of_birth(date_input: str | StufBgIncompleteDateType) -> str:
    """
    Return a valid date (str) or None depending on the data we retrieve.

    StUF-BG returns multiple types of date. The data we retrieve for the date may be
    incomplete so there are four different ways to see what data is missing (or not)
    from the date. The "indOnvolledigeDatum" is the attribute that defines that.

    "M": only year known
    "D": year/month known
    "J": date exists but no individual parts known
    "V": full date
    """
    if isinstance(date_input, str):
        # the date coming from the stuf_bg is of type '20200909' so we have to make it an
        # iso-8601 type
        return format_date_value(date_input)

    date_text = date_input.get("#text")
    return date_text if date_text else ""


def fromstring(content: str | bytes):
    """
    Create an LXML etree from the string content without resolving entities.

    Resolving entities is a security risk, which is why we disable it.
    Inspired by https://github.com/mvantellingen/python-zeep/pull/1179/ as their solution
    for the deprecated defusedxml.lxml module and the defaults applied in defusedxml.lxml.
    """
    parser = XMLParser(resolve_entities=False)
    return _fromstring(content, parser=parser)


def datetime_in_amsterdam(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return value
    return timezone.make_naive(value, timezone=TIMEZONE_AMS)


def get_today() -> date:
    now = datetime_in_amsterdam(timezone.now())
    return now.date()
