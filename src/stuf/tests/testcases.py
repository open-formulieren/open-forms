from django.test import TestCase


class StUFAssertionsMixin:
    namespaces: dict = {}  # subclasses should set this as a class attribute

    def assertXPathExists(self, xml_doc, xpath):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        if len(elements) == 0:
            self.fail(f"cannot find XML element(s) with xpath {xpath}")

    def assertXPathNotExists(self, xml_doc, xpath):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        if len(elements) != 0:
            self.fail(
                f"found {len(elements)} unexpected XML element(s) with xpath {xpath}"
            )

    def assertXPathCount(self, xml_doc, xpath, count):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        self.assertEqual(
            len(elements),
            count,
            f"cannot find exactly {count} XML element(s) with xpath {xpath}",
        )

    def assertXPathEqual(self, xml_doc, xpath, text):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        self.assertGreaterEqual(
            len(elements), 1, f"cannot find XML element(s) with xpath {xpath}"
        )
        self.assertEqual(
            len(elements), 1, f"multiple XML element(s) found for xpath {xpath}"
        )
        if isinstance(elements[0], str):
            self.assertEqual(elements[0].strip(), text, f"at xpath {xpath}")
        else:
            elem_text = elements[0].text
            if elem_text is None:
                elem_text = ""
            else:
                elem_text = elem_text.strip()
            self.assertEqual(elem_text, text, f"at xpath {xpath}")

    def assertXPathEqualDict(self, xml_doc, path_value_dict):
        for path, value in path_value_dict.items():
            self.assertXPathEqual(xml_doc, path, value)

    def assertXPathContainsAll(self, xml_doc, xpath, expected_values):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        self.assertGreaterEqual(
            len(elements), 1, f"cannot find XML element(s) with xpath {xpath}"
        )

        texts = []
        for el in elements:
            if isinstance(el, str):
                texts.append(el.strip())
            else:
                elem_text = (el.text or "").strip()
                texts.append(elem_text)

        for val in expected_values:
            self.assertIn(val, texts, f"Expected '{val}' in {texts} at xpath {xpath}")

    def assertXPathContainsDict(self, xml_doc, path_values_dict):
        for path, values in path_values_dict.items():
            if not isinstance(values, list):
                values = [values]
            self.assertXPathContainsAll(xml_doc, path, values)

    def assertSoapXMLCommon(self, xml_doc):
        self.assertIsNotNone(xml_doc)
        self.assertXPathExists(
            xml_doc, "/*[local-name()='Envelope']/*[local-name()='Header']"
        )
        self.assertXPathExists(
            xml_doc, "/*[local-name()='Envelope']/*[local-name()='Body']"
        )


class StUFTestBase(StUFAssertionsMixin, TestCase):
    pass
