from contextlib import contextmanager

from playwright.async_api import Page, expect


@contextmanager
def phase(desc: str):
    yield


async def open_component_options_modal(page: Page, label: str, exact: bool = False):
    """
    Find the component in the builder with the given label and click the edit icon
    to bring up the options modal.
    """
    # hover over component to bring up action icons
    await page.get_by_text(label, exact=exact).hover()
    # formio doesn't have accessible roles here, so use CSS selector
    await page.locator('css=[ref="editComponent"]').locator("visible=true").last.click()
    # check that the modal is open now
    await expect(page.locator("css=.formio-dialog-content")).to_be_visible()


async def close_modal(page: Page, button_text: str, **kwargs):
    modal = page.locator("css=.formio-dialog-content")
    await modal.get_by_role("button", name=button_text, **kwargs).click()
    await expect(modal).to_be_hidden()
