import json
from collections import OrderedDict

from django.http.request import RawPostDataException
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from debug_toolbar.forms import SignedDataForm
from debug_toolbar.panels import Panel
from debug_toolbar.panels.history import views
from debug_toolbar.panels.history.forms import HistoryStoreForm


class HistoryPanel(Panel):
    """ A panel to display History """

    title = _("History")
    nav_title = _("History")
    template = "debug_toolbar/panels/history.html"

    @property
    def is_historical(self):
        """The HistoryPanel should not be included in the historical panels."""
        return False

    @classmethod
    def get_urls(cls):
        return [
            path("history_sidebar/", views.history_sidebar, name="history_sidebar"),
            path("history_refresh/", views.history_refresh, name="history_refresh"),
        ]

    @property
    def nav_subtitle(self):
        return self.get_stats().get("request_url", "")

    def generate_stats(self, request, response):
        try:
            if request.method == "GET":
                data = request.GET.copy()
            else:
                data = request.POST.copy()
            # GraphQL tends to not be populated in POST. If the request seems
            # empty, check if it's a JSON request.
            if (
                not data
                and request.body
                and request.META.get("CONTENT_TYPE") == "application/json"
            ):
                try:
                    data = json.loads(request.body)
                except ValueError:
                    pass
        except RawPostDataException:
            # It is not guaranteed that we may read the request data (again).
            data = None

        self.record_stats(
            {
                "request_url": request.get_full_path(),
                "request_method": request.method,
                "data": data,
                "time": timezone.now(),
            }
        )

    @property
    def content(self):
        """Content of the panel when it's displayed in full screen.

        Fetch every store for the toolbar and include it in the template.
        """
        stores = OrderedDict()
        for id, toolbar in reversed(self.toolbar._store.items()):
            stores[id] = {
                "toolbar": toolbar,
                "form": SignedDataForm(
                    initial=HistoryStoreForm(initial={"store_id": id}).initial
                ),
            }

        return render_to_string(
            self.template,
            {
                "current_store_id": self.toolbar.store_id,
                "stores": stores,
                "refresh_form": SignedDataForm(
                    initial=HistoryStoreForm(
                        initial={"store_id": self.toolbar.store_id}
                    ).initial
                ),
            },
        )

    @property
    def scripts(self):
        scripts = super().scripts
        scripts.append(static("debug_toolbar/js/history.js"))
        return scripts
