import json
from contextlib import contextmanager

from playwright.async_api import Locator, Page, expect

from openforms.typing import JSONValue


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


async def click_modal_button(page: Page, button_text: str, **kwargs):
    modal = page.locator("css=.formio-dialog-content")
    await modal.get_by_role("button", name=button_text, **kwargs).click()
    return modal


async def close_modal(page: Page, button_text: str, **kwargs):
    modal = await click_modal_button(page, button_text, **kwargs)
    await expect(modal).to_be_hidden()


async def enter_json_in_editor(
    page: Page, editor: Locator, expression: JSONValue
) -> None:
    """
    Put some JSON into a monaca-json-editor instance.

    :arg locator: The locator (`page.locator(".monaco-editor")`) pointing to the
      editor instance.
    :arg expression: The JSON expression. Will be serialized to JSON before putting it
      in the input.
    """
    await expect(editor).to_be_visible()
    code = json.dumps(expression)
    # put the code in the clipboard and do a paste event
    await page.evaluate("text => navigator.clipboard.writeText(text)", code)
    # click the editor to focus it
    await editor.click()
    # select all
    await page.keyboard.press("ControlOrMeta+KeyA")
    # and replace with paste
    await page.keyboard.press("ControlOrMeta+KeyV")


async def check_json_in_editor(editor: Locator, expected_value: JSONValue):
    await expect(editor).to_be_visible()
    code_content = editor.locator(".lines-content")
    code_in_editor = await code_content.text_content() or ""
    # monaco uses &nbsp; (= "\xa0") for indentation, which we need to strip out
    code = code_in_editor.replace("\xa0", "")
    try:
        _json = json.loads(code)
    except json.JSONDecodeError as exc:
        raise AssertionError("code is not valid JSON") from exc
    assert _json == expected_value, "Code in editor is not equivalent"
