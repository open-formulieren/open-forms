from typing import Any

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import structlog
from cookie_consent.admin import LogItemAdmin as CookieLogAdmin
from cookie_consent.models import LogItem as CookieLog
from cspreports.admin import CSPReportAdmin
from cspreports.models import CSPReport
from log_outgoing_requests.admin import OutgoingRequestsLogAdmin
from log_outgoing_requests.models import OutgoingRequestsLog

from openforms.logging import audit_logger
from openforms.typing import is_authenticated_request

logger = structlog.stdlib.get_logger()


class SubmitActions(models.TextChoices):
    save = "_save", _("Save")
    add_another = "_addanother", _("Save and add another")
    edit_again = "_continue", _("Save and continue editing")


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


def replace_cookie_log_admin():
    # defaults to True
    if getattr(settings, "COOKIE_CONSENT_LOG_ENABLED", True):

        class LogAdmin(ReadOnlyAdminMixin, CookieLogAdmin):
            pass

        admin.site.unregister(CookieLog)
        admin.site.register(CookieLog, LogAdmin)


class CSPReportOverrideAdmin(ReadOnlyAdminMixin, CSPReportAdmin):
    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj=obj)

    def json_as_html(self, instance):
        # needs another round of mark_safe even though the parent class already does it
        return mark_safe(super().json_as_html(instance))


admin.site.unregister(CSPReport)
admin.site.register(CSPReport, CSPReportOverrideAdmin)


class OutgoingRequestsLogOverrideAdmin(OutgoingRequestsLogAdmin):
    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        assert is_authenticated_request(request)
        outgoing_request_log = self.get_object(request, object_id)
        if outgoing_request_log is None:
            raise Http404(f"No {self.model._meta.object_name} matches the given query.")
        audit_logger.info(
            "outgoing_request_log_details_view_admin",
            object_id=object_id,
            user=request.user.username,
        )
        return super().change_view(request, object_id, form_url, extra_context)


admin.site.unregister(OutgoingRequestsLog)
admin.site.register(OutgoingRequestsLog, OutgoingRequestsLogOverrideAdmin)
