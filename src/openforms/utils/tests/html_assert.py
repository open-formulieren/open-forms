import re


class HTMLAssertMixin:
    def assertTagWithTextIn(self, tag, text, document_str):
        """
        check for html tags and their content while ignoring tag attributes
        """
        if not re.search(f"<{tag}(?: [^>]*)?>\s*{text}", document_str):
            self.fail(f"cannot find <{tag}..>{text} in: {document_str}")

    def assertNotTagWithTextIn(self, tag, text, document_str):
        """
        check for html tags and their content while ignoring tag attributes
        """
        if re.search(f"<{tag}(?: [^>]*)?>\s*{text}", document_str):
            self.fail(f"unexpectedly found <{tag}..>{text} in: {document_str}")
