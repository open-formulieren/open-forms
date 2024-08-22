from django.db import models
from django.utils.translation import gettext_lazy as _


class ObjectsAPIAttributes(models.TextChoices):
    url = "url", _("Url")
    uuid = "uuid", _("UUID")
    type = "type", _("Type")
    record_index = "record.index", _("Record > Index")
    record_typeVersion = "record.typeVersion", _("Record > Type version")

    record_data_ = "", _("Record > Data")

    record_geometry = "record.geometry", _("Record > Geometry")
    record_startAt = "record.startAt", _("Record > Start at")
    record_endAt = "record.endAt", _("Record > End at")
    record_registrationAt = "record.registrationAt", _("Record > Registration at")
    record_correctionFor = "record.correctionFor", _("Record > Correction for")
    record_correctedBy = "record_correctedBy", _("Record > Corrected by")
