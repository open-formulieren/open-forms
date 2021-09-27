from django.utils.translation import gettext_lazy as _, ngettext

import requests
import requests_mock
from debug_toolbar.panels import Panel
from requests.sessions import preferred_clock
from requests_mock import adapter, exceptions
from requests_mock.mocker import _original_send

# TODO: persist data over requests - POST followed by redirect does not display the
# API calls made.


def extract_intervals(request_history):
    """
    Extract the continuous (start, end) intervals during which network IO happend.

    Summing the duration of those intervals gives the total API call time as perceived
    by the end-user (taking into account parallel requests using concurrency features).
    """
    if not request_history:
        return []

    # first - sort by request start time and end time, this allows us to order the
    # requests on the actual timeline.
    timings = sorted(
        [req.timing for req in request_history],
        key=lambda timing: (timing[0], timing[1]),
    )

    distinct_intervals = []
    min_start, max_end = timings[0][:2]

    for timing in timings:
        start, end = timing[0], timing[1]
        if start <= max_end and end > max_end:
            max_end = timing[1]

        if start > max_end:
            distinct_intervals.append((min_start, max_end))
            min_start, max_end = timing[:2]

    # last loop iteration doesn't append distinct interval
    distinct_intervals.append((min_start, max_end))

    return distinct_intervals


def calculate_total_time(request_history) -> int:
    distinct_intervals = extract_intervals(request_history)

    if not distinct_intervals:
        return 0

    total_time = 0
    for interval in distinct_intervals:
        total_time += interval[1] - interval[0]

    return int(total_time * 1000)


class PanelMocker(requests_mock.Mocker):
    def start(self):
        """Start mocking requests.

        Install the adapter and the wrappers required to intercept requests.
        """
        # attribute changed in 1.8.0
        real_http = self.real_http if hasattr(self, "real_http") else self._real_http

        if self._last_send:
            raise RuntimeError("Mocker has already been started")

        self._last_send = requests.Session.send

        def _fake_get_adapter(session, url):
            return self._adapter

        def _fake_send(session, request, **kwargs):
            real_get_adapter = requests.Session.get_adapter
            requests.Session.get_adapter = _fake_get_adapter

            # NOTE(jamielennox): self._last_send vs _original_send. Whilst it
            # seems like here we would use _last_send there is the possibility
            # that the user has messed up and is somehow nesting their mockers.
            # If we call last_send at this point then we end up calling this
            # function again and the outer level adapter ends up winning.
            # All we really care about here is that our adapter is in place
            # before calling send so we always jump directly to the real
            # function so that our most recently patched send call ends up
            # putting in the most recent adapter. It feels funny, but it works.

            start = preferred_clock()

            try:
                return _original_send(session, request, **kwargs)
            except exceptions.NoMockAddress:
                if not real_http:
                    raise
            except adapter._RunRealHTTP:
                # this mocker wants you to run the request through the real
                # requests library rather than the mocking. Let it.
                pass
            finally:
                requests.Session.get_adapter = real_get_adapter

            req = next(r for r in self.request_history if r._request == request)

            try:
                response = _original_send(session, request, **kwargs)
            except Exception:
                response = None
                raise
            else:
                req.status_code = response.status_code
            finally:
                duration = (
                    response.elapsed.total_seconds() if response is not None else 0
                )
                end = start + duration  # approximate
                req.timing = (start, end, int(duration * 1000))
            return response

        requests.Session.send = _fake_send


class APICallsPanel(Panel):
    """
    Django Debug Toolbar panel to track python-requests calls.
    """

    title = _("API calls")
    template = "ddt_api_calls/requests.html"

    def enable_instrumentation(self):
        self.mocker = PanelMocker(real_http=True)
        if not self.toolbar.request.is_ajax():
            self.mocker.start()

    def disable_instrumentation(self):
        if not self.toolbar.request.is_ajax():
            self.mocker.stop()

    @property
    def nav_subtitle(self) -> str:
        num_calls = len(self.mocker.request_history)
        total_time = calculate_total_time(self.mocker.request_history)
        return ngettext(
            "1 API call made in {duration}ms",
            "{n} API calls made in {duration}ms",
            num_calls,
        ).format(n=num_calls, duration=total_time)

    def generate_stats(self, request, response):
        requests = sorted(
            self.mocker.request_history,
            key=lambda req: (req.timing[0], req.timing[1]),
        )

        unique_keys = [(request.method, request.url) for request in requests]
        duplicated = [
            request
            for request in requests
            if unique_keys.count((request.method, request.url)) > 1
        ]

        if requests:
            min_start = min(req.timing[0] for req in requests)
            max_end = max(req.timing[1] for req in requests)
            total_time = max_end - min_start

            if total_time > 0:
                # annotate each request with 'idle' and 'wait'
                for request in requests:
                    request.idle = round(
                        ((request.timing[0] - min_start) / total_time) * 100, 2
                    )
                    request.wait = round(
                        ((request.timing[1] - request.timing[0]) / total_time) * 100, 2
                    )
                    request.tail = 100 - request.idle - request.wait
        else:
            total_time = 0

        stats = {
            "requests": requests,
            "duplicated": duplicated,
        }
        self.record_stats(stats)
