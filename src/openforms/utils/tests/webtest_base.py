class WebTestPyQueryMixin:
    def assertPyQueryExists(self, response, query):
        pq = response.pyquery(query)
        pl = len(pq)
        if not pl:
            self.fail(f"zero matching elements found for: {query}")
        return pq

    def assertPyQueryNotExists(self, response, query):
        pl = len(response.pyquery(query))
        if pl:
            self.fail(
                f"expected zero elements but found {pl} matching elements for: {query}"
            )

    def assertPyQueryOnce(self, response, query):
        pl = len(response.pyquery(query))
        if pl != 1:
            self.fail(
                f"expected exactly one but found {pl} matching elements for: {query}"
            )

    def assertPyQueryCount(self, response, query, count):
        pl = len(response.pyquery(query))
        if pl != count:
            self.fail(
                f"expected exactly {count} but found {pl}  atching elements for: {query}"
            )
