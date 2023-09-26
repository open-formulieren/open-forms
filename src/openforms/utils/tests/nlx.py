from unittest.mock import patch


class DisableNLXRewritingMixin:
    """
    Disable NLX rewriting.

    This is especially useful when you want to keep using SimpleTestCase, as the
    rewriter queries the database for rewrite targets.
    """

    def setUp(self):
        patchers = (
            patch("zgw_consumers.nlx.Rewriter._rewrite", new=lambda *args: None),
            patch("zgw_consumers.nlx.Rewriter.reverse_rewrites", new=[]),
        )
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        super().setUp()
