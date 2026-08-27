import json
from contextlib import contextmanager
from unittest import skipIf

from playwright.async_api import Locator, Page, expect

from openforms.tests.e2e.base import BROWSER
from openforms.typing import JSONValue


@contextmanager
def phase(desc: str):
    yield


async def drag_and_drop_component(page: Page, component: str, nth: int | None = None):
    draggable_button = page.get_by_role("button", name=component, exact=True)
    if nth is not None:
        draggable_button = draggable_button.locator(f"nth={nth}")

    await draggable_button.hover()
    await page.mouse.down()
    # This is added to make it work for when there is already a component in the container.
    # Idea taken from: https://playwright.dev/python/docs/input#dragging-manually
    # It says:
    # "If your page relies on the dragover event being dispatched, you need at least two mouse moves to trigger it in
    # all browsers. To reliably issue the second mouse move, repeat your mouse.move() or locator.hover() twice."
    # ... but repeating the hover didn't work. Hence, the extra move.
    # await page.mouse.move(0, 0)

    drag_target = page.get_by_test_id("main-dropzone")
    await drag_target.scroll_into_view_if_needed()
    await drag_target.hover()
    await drag_target.hover()

    # move the pointer a bit to ensure we fire the dragover event - similar to the builder
    # patch with some requestAnimationFrame shenanigans
    target_box = await drag_target.bounding_box()
    assert target_box is not None
    target_center_x, target_center_y = (
        target_box["x"] + target_box["width"] / 2,
        -target_box["y"] + target_box["height"] / 2,
    )
    await page.mouse.move(target_center_x - 10, target_center_y - 10, steps=3)
    await page.mouse.up()


async def open_fieldset(page: Page, title: str) -> None:
    """
    Toggle a fieldset from collapsed to open state.

    :param page: The playwright page to find elements in.
    :param title: The heading/title of the fieldset displayed on the page, inside the
      summary element.
    """
    toggle_summary = page.get_by_role("heading", level=2, name=title)
    await toggle_summary.click()


async def open_component_options_modal(page: Page, label: str, exact: bool = False):
    """
    Find the component in the builder with the given label and click the edit icon
    to bring up the options modal.
    """
    # hover over component to bring up action icons
    await page.get_by_text(label, exact=exact).hover()
    await (
        page.get_by_role("button", name="Edit component")
        .filter(visible=True)
        .last.click()
    )
    # check that the modal is open now
    await expect(page.get_by_role("dialog")).to_be_visible()


async def click_modal_button(page: Page, button_text: str, **kwargs):
    modal = page.get_by_role("dialog")
    await modal.get_by_role("button", name=button_text, **kwargs).click()
    return modal


async def close_modal(page: Page, button_text: str, **kwargs):
    modal = await click_modal_button(page, button_text, **kwargs)
    await expect(modal).to_be_hidden()


skip_on_webtest = skipIf(
    BROWSER == "webkit", "Skip test on Webkit browser (because it is known to not work)"
)


def _raise_for_webkit():
    if BROWSER == "webkit":
        raise Exception(  # noqa: TRY002
            "This functionality does not work on Webkit with Playwright. Best is to "
            "conditionally skip the test with @skip_on_webtest."
        )


async def enter_json_in_editor(
    page: Page, editor: Locator, expression: JSONValue
) -> None:
    """
    Put some JSON into a monaca-json-editor instance.

    :param locator: The locator (`page.locator(".monaco-editor")`) pointing to the
      editor instance.
    :param expression: The JSON expression. Will be serialized to JSON before putting it
      in the input.
    """
    # copy-and-paste does work on Webkit, but I can't get selecting all editor content
    # and replacing it with the pasted content to work :(
    _raise_for_webkit()

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
    # copy-and-paste does work on Webkit, but I can't get selecting all editor content
    # and replacing it with the pasted content to work :(
    _raise_for_webkit()

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
