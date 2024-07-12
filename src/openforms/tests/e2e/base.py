import os
from contextlib import asynccontextmanager
from typing import Any, Literal, TypeAlias

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings, tag
from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from maykin_2fa.test import disable_admin_mfa
from playwright.async_api import BrowserType, Page, async_playwright

from openforms.accounts.tests.factories import SuperUserFactory

SupportedBrowser: TypeAlias = Literal["chromium", "firefox", "webkit"]

HEADLESS = "NO_E2E_HEADLESS" not in os.environ
BROWSER: SupportedBrowser = os.getenv("E2E_DRIVER", default="chromium")  # type:ignore
SLOW_MO = int(os.environ.get("SLOW_MO", "100"))
PLAYWRIGHT_BROWSERS_PATH = os.getenv("PLAYWRIGHT_BROWSERS_PATH", default=None)

LAUNCH_KWARGS = {
    "headless": HEADLESS,
    "slow_mo": SLOW_MO,
    "executable_path": PLAYWRIGHT_BROWSERS_PATH,
}

BROWSER_PERMISSIONS: dict[SupportedBrowser, list[str]] = {
    "chromium": ["clipboard-read", "clipboard-write"],
}


@sync_to_async
def create_superuser(**kwargs):
    kwargs.setdefault("username", "admin")
    kwargs.setdefault("password", "e2tests")
    SuperUserFactory.create(**kwargs)


@asynccontextmanager
async def browser_page():
    context_kwargs: dict[str, Any] = {
        "locale": "en-UK",
        "timezone_id": "Europe/Amsterdam",
    }
    if permissions := BROWSER_PERMISSIONS.get(BROWSER):
        context_kwargs["permissions"] = permissions

    async with async_playwright() as p:
        try:
            _browser: BrowserType = getattr(p, BROWSER)
            browser = await _browser.launch(**LAUNCH_KWARGS)
            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()
            yield page
        finally:
            await browser.close()


@tag("e2e")
@disable_admin_mfa()
@override_settings(ALLOWED_HOSTS=["*"])
class E2ETestCase(StaticLiveServerTestCase):
    async def _admin_login(self, page: Page) -> None:
        login_url = furl(self.live_server_url) / reverse("admin-mfa-login")
        await page.goto(str(login_url))
        await page.get_by_label("Username").fill("admin")
        await page.get_by_label("Password").fill("e2tests")

        await page.get_by_role("button", name="Log in").click()
