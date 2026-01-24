import lxml.html


class InlineStylesMixin:
    def _parse_html(self, html: str) -> tuple:
        root = lxml.html.fromstring(html)
        # lxml normalizes the markup and moves the inline style tag to the HEAD node
        # style tags in the <body> is technically not valid, pre HTML 5.2. See also
        # https://stackoverflow.com/a/4607092
        style_element = root.find("head").find("style")
        body = root.find("body")
        assert body is not None
        content = body.getchildren() or body.text
        return style_element, content

    def assertStyleNonce(self, style, nonce: str):
        nonce_attrib = style.attrib.get("nonce")
        self.assertEqual(nonce_attrib, nonce)

    def assertNoInlineStyles(self, content):
        for node in content:
            with self.subTest(node=node):
                style_attrib = node.attrib.get("style", False)
                self.assertFalse(style_attrib, f"Inline style '{style_attrib}' found")
