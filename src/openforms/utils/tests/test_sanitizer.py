import io

from django.core.files import File
from django.test import SimpleTestCase

from ..sanitizer import sanitize_svg_content, sanitize_svg_file


class SanitizeSvgFileTests(SimpleTestCase):
    def test_sanitize_svg_content_removes_script_tags(self):
        bad_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green" />
            <script>//<![CDATA[
                alert("I am malicious >:)")
            //]]></script>
            <g>
                <rect class="btn" x="0" y="0" width="10" height="10" fill="red" />
            </g>
        </svg>
        """
        sanitized_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green"></circle>
            <g>
                <rect x="0" y="0" width="10" height="10" fill="red"></rect>
            </g>
        </svg>
        """

        temp_file = io.BytesIO(bad_svg_content.encode("utf-8"))

        # Assert that sanitize_svg_content removed the script tag
        sanitized_svg_file = sanitize_svg_file(File(temp_file))
        self.assertHTMLEqual(
            sanitized_svg_file.read().decode("utf-8"),
            sanitized_svg_content,
        )


class SanitizeSvgContentTests(SimpleTestCase):
    def test_sanitize_svg_content_removes_script_tags(self):
        bad_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green" />
            <script>//<![CDATA[
                alert("I am malicious >:)")
            //]]></script>
            <g>
                <rect class="btn" x="0" y="0" width="10" height="10" fill="red" />
            </g>
        </svg>
        """
        sanitized_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green"></circle>
            <g>
                <rect x="0" y="0" width="10" height="10" fill="red"></rect>
            </g>
        </svg>
        """

        # Assert that sanitize_svg_content removed the script tag
        sanitized_bad_svg_content = sanitize_svg_content(bad_svg_content)
        self.assertHTMLEqual(sanitized_svg_content, sanitized_bad_svg_content)

    def test_sanitize_svg_content_removes_event_handlers(self):
        bad_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green" onclick="alert('forget about me?')" />
            <g>
                <rect class="btn" x="0" y="0" width="10" height="10" fill="red" onload="alert('click!')" />
            </g>
        </svg>
        """
        sanitized_svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="25" fill="green"></circle>
            <g>
                <rect x="0" y="0" width="10" height="10" fill="red"></rect>
            </g>
        </svg>
        """

        # Assert that sanitize_svg_content removed the event handlers
        sanitized_bad_svg_content = sanitize_svg_content(bad_svg_content)
        self.assertHTMLEqual(sanitized_svg_content, sanitized_bad_svg_content)
