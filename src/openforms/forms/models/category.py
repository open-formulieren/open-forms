import uuid as _uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from treebeard.mp_tree import MP_Node


class Category(MP_Node):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)

    name = models.CharField(
        _("name"), max_length=64, help_text=_("Human readable name")
    )

    node_order_by = ["name"]

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name
