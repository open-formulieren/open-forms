"""
The main DebugToolbar class that loads and renders the Toolbar.
"""

import uuid
from collections import OrderedDict

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.urls import path, resolve
from django.urls.exceptions import Resolver404
from django.utils.module_loading import import_string

from debug_toolbar import settings as dt_settings


class DebugToolbar:
    def __init__(self, request, get_response):
        self.request = request
        self.config = dt_settings.get_config().copy()
        panels = []
        for panel_class in reversed(self.get_panel_classes()):
            panel = panel_class(self, get_response)
            panels.append(panel)
            if panel.enabled:
                get_response = panel.process_request
        self.process_request = get_response
        self._panels = OrderedDict()
        while panels:
            panel = panels.pop()
            self._panels[panel.panel_id] = panel
        self.stats = {}
        self.server_timing_stats = {}
        self.store_id = None

    # Manage panels

    @property
    def panels(self):
        """
        Get a list of all available panels.
        """
        return list(self._panels.values())

    @property
    def enabled_panels(self):
        """
        Get a list of panels enabled for the current request.
        """
        return [panel for panel in self._panels.values() if panel.enabled]

    def get_panel_by_id(self, panel_id):
        """
        Get the panel with the given id, which is the class name by default.
        """
        return self._panels[panel_id]

    # Handle rendering the toolbar in HTML

    def render_toolbar(self):
        """
        Renders the overall Toolbar with panels inside.
        """
        if not self.should_render_panels():
            self.store()
        try:
            context = {"toolbar": self}
            return render_to_string("debug_toolbar/base.html", context)
        except TemplateSyntaxError:
            if not apps.is_installed("django.contrib.staticfiles"):
                raise ImproperlyConfigured(
                    "The debug toolbar requires the staticfiles contrib app. "
                    "Add 'django.contrib.staticfiles' to INSTALLED_APPS and "
                    "define STATIC_URL in your settings."
                )
            else:
                raise

    def should_render_panels(self):
        render_panels = self.config["RENDER_PANELS"]
        if render_panels is None:
            render_panels = self.request.META["wsgi.multiprocess"]
        return render_panels

    # Handle storing toolbars in memory and fetching them later on

    _store = OrderedDict()

    def store(self):
        # Store already exists.
        if self.store_id:
            return
        self.store_id = uuid.uuid4().hex
        self._store[self.store_id] = self
        for _ in range(self.config["RESULTS_CACHE_SIZE"], len(self._store)):
            self._store.popitem(last=False)

    @classmethod
    def fetch(cls, store_id):
        return cls._store.get(store_id)

    # Manually implement class-level caching of panel classes and url patterns
    # because it's more obvious than going through an abstraction.

    _panel_classes = None

    @classmethod
    def get_panel_classes(cls):
        if cls._panel_classes is None:
            # Load panels in a temporary variable for thread safety.
            panel_classes = [
                import_string(panel_path) for panel_path in dt_settings.get_panels()
            ]
            cls._panel_classes = panel_classes
        return cls._panel_classes

    _urlpatterns = None

    @classmethod
    def get_urls(cls):
        if cls._urlpatterns is None:
            from . import views

            # Load URLs in a temporary variable for thread safety.
            # Global URLs
            urlpatterns = [
                path("render_panel/", views.render_panel, name="render_panel")
            ]
            # Per-panel URLs
            for panel_class in cls.get_panel_classes():
                urlpatterns += panel_class.get_urls()
            cls._urlpatterns = urlpatterns
        return cls._urlpatterns

    @classmethod
    def is_toolbar_request(cls, request):
        """
        Determine if the request is for a DebugToolbar view.
        """
        # The primary caller of this function is in the middleware which may
        # not have resolver_match set.
        try:
            resolver_match = request.resolver_match or resolve(request.path)
        except Resolver404:
            return False
        return resolver_match.namespaces and resolver_match.namespaces[-1] == app_name


app_name = "djdt"
urlpatterns = DebugToolbar.get_urls()
