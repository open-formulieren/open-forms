from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

SUBMISSIONS_SESSION_KEY = "form-submissions"

# Source: https://stackoverflow.com/a/54086404
URL_REGEX = r"(?:(?:https?|ftp):\/\/|\b(?:[a-z\d]+\.))(?:(?:[^\s()<>]+|\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))?\))+(?:\((?:[^\s()<>]+|(?:\(?:[^\s()<>]+\)))?\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))?"


class RegistrationStatuses(DjangoChoices):
    pending = ChoiceItem("pending", _("Pending (not registered yet)"))
    success = ChoiceItem("success", _("Success"))
    failed = ChoiceItem("failed", _("Failed"))
