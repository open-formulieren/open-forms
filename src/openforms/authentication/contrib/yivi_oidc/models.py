from django.db import models
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField


class AttributeGroup(models.Model):
    name = models.CharField(
        _("group name"),
        max_length=100,
        unique=True,
        help_text=_(
            "A human-readable name for the group of attributes, used in the form "
            "configuration."
        ),
    )
    description = models.CharField(
        _("group description"),
        max_length=200,
        help_text=_(
            "A longer human-readable description for the group of attributes, used in "
            "the form configuration."
        ),
        blank=True,
    )
    attributes = ArrayField(
        base_field=models.CharField(
            _("attribute"),
            max_length=100,
            blank=True,
        ),
        default=list,
        verbose_name=_("attributes"),
        blank=True,
        help_text=_(
            "List of attributes that will be requested from the user. The user can "
            "choose whether to grant access to all these attributes, or none. If you "
            "want individually optional attributes, you should define them as separate "
            "attribute groups."
        ),
    )

    class Meta:
        verbose_name = _("yivi attribute group")
        verbose_name_plural = _("yivi attribute groups")

    def __str__(self):
        return self.name
