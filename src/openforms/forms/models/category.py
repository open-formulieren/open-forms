import uuid as _uuid

from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from furl import furl
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

    def get_admin_changelist_link(self, model, *, text=None, field_name="category"):
        url = self.get_admin_changelist_url(model, field_name=field_name)
        text = text or self.name
        link = format_html('<a href="{url}">{text}</a>', url=url, text=text)
        return link

    def get_admin_changelist_url(self, model, *, field_name="category"):
        url = reverse(
            "admin:%s_%s_changelist" % (model._meta.app_label, model._meta.model_name),
        )
        f = furl(url)
        f.args[f"{field_name}__id__exact"] = self.id
        return str(f)

    def get_edit_link(self):
        url = reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=[self.id],
        )
        text = _("Edit category")
        link = format_html('<a href="{url}">{text}</a>', url=url, text=text)
        return link

    def get_branch_ids(self):
        return [self.id] + [c.id for c in self.get_descendants()]

    def __str__(self):
        return self.name
