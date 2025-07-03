from urllib.parse import quote as urlquote

from django.contrib import messages
from django.contrib.admin.utils import quote
from django.contrib.auth import get_permission_codename
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from rest_framework.request import Request

from openforms.utils.admin import SubmitActions


def has_change_permission(user, obj: models.Model) -> bool:
    opts = obj._meta
    codename = get_permission_codename("change", opts)
    return user.has_perm(f"{opts.app_label}.{codename}")


def get_obj_repr(user, obj: models.Model) -> str:
    opts = obj._meta
    if has_change_permission(user, obj):
        obj_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change",
            args=(quote(obj.pk),),
        )
        obj_repr = format_html('<a href="{}">{}</a>', urlquote(obj_url), obj)
    else:
        obj_repr = str(obj)

    return obj_repr


MESSAGE_TEMPLATES = {
    (SubmitActions.save, True): lambda: _('The {name} "{obj}" was added successfully.'),
    (SubmitActions.save, False): lambda: _(
        'The {name} "{obj}" was changed successfully.'
    ),
    (SubmitActions.edit_again, True): lambda: _(
        'The {name} "{obj}" was added successfully.'
    ),
    (SubmitActions.edit_again, False): lambda: _(
        'The {name} "{obj}" was changed successfully. You may edit it again below.'
    ),
    (SubmitActions.add_another, True): lambda: _(
        'The {name} "{obj}" was added successfully. You may add another {name} below.'
    ),
    (SubmitActions.add_another, False): lambda: _(
        'The {name} "{obj}" was changed successfully. You may add another {name} below.'
    ),
}


def add_success_message(
    request: HttpRequest | Request,
    instance: models.Model,
    submit_action: str,
    is_new: bool,
):
    obj_repr = get_obj_repr(request.user, instance)
    name = instance._meta.verbose_name

    template = MESSAGE_TEMPLATES[(submit_action, is_new)]()

    if submit_action == SubmitActions.edit_again and is_new:
        if has_change_permission(request.user, instance):
            template += " " + _("You may edit it again below.")

    msg = format_html(template, name=name, obj=obj_repr)
    messages.success(request, msg)
