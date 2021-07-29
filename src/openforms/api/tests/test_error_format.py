from django.utils.translation import gettext as _

from rest_framework.test import APIRequestFactory, APITestCase

from . import error_views as views


class ExceptionHandlerTests(APITestCase):
    """
    Test the error handling responses
    """

    maxDiff = None
    factory = APIRequestFactory()

    def assertErrorResponse(self, view, expected_data: dict):
        _view = view.as_view()
        # method doesn't matter since we're using `dispatch`
        request = self.factory.get("/some/irrelevant/url")

        response = _view(request)

        expected_status = expected_data["status"]
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response["Content-Type"], "application/problem+json")

        # can't verify UUID...
        self.assertTrue(response.data["instance"].startswith("urn:uuid:"))
        del response.data["instance"]

        exc_class = view.exception.__class__.__name__
        expected_data["type"] = f"http://testserver/fouten/{exc_class}/"
        self.assertEqual(response.data, expected_data)

    def test_400_error(self):
        self.assertErrorResponse(
            views.ValidationErrorView,
            {
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "invalid_params": [
                    {
                        "name": "foo",
                        "code": "validation-error",
                        "reason": _("Invalid data."),
                    }
                ],
            },
        )

    def test_401_error(self):
        self.assertErrorResponse(
            views.NotAuthenticatedView,
            {
                "code": "not_authenticated",
                "title": _("Authentication credentials were not provided."),
                "status": 401,
                "detail": _("Authentication credentials were not provided."),
            },
        )

    def test_403_error(self):
        self.assertErrorResponse(
            views.PermissionDeniedView,
            {
                "code": "permission_denied",
                "title": _("You do not have permission to perform this action."),
                "status": 403,
                "detail": _("This action is not allowed"),
            },
        )

    def test_404_error(self):
        self.assertErrorResponse(
            views.NotFoundView,
            {
                "code": "not_found",
                "title": _("Not found."),
                "status": 404,
                "detail": _("Some detail message"),
            },
        )

    def test_405_error(self):
        self.assertErrorResponse(
            views.MethodNotAllowedView,
            {
                "code": "method_not_allowed",
                "title": _('Method "{method}" not allowed.'),
                "status": 405,
                "detail": _('Method "{method}" not allowed.').format(method="GET"),
            },
        )

    def test_406_error(self):
        self.assertErrorResponse(
            views.NotAcceptableView,
            {
                "code": "not_acceptable",
                "title": _("Could not satisfy the request Accept header."),
                "status": 406,
                "detail": _("Content negotation failed"),
            },
        )

    def test_409_error(self):
        self.assertErrorResponse(
            views.ConflictView,
            {
                "code": "conflict",
                "title": _("A conflict occurred"),
                "status": 409,
                "detail": _("The resource was updated, please retrieve it again"),
            },
        )

    def test_410_error(self):
        self.assertErrorResponse(
            views.GoneView,
            {
                "code": "gone",
                "title": _("The resource is gone"),
                "status": 410,
                "detail": _("The resource was destroyed"),
            },
        )

    def test_412_error(self):
        self.assertErrorResponse(
            views.PreconditionFailed,
            {
                "code": "precondition_failed",
                "title": _("Precondition failed"),
                "status": 412,
                "detail": _("Something about CRS"),
            },
        )

    def test_415_error(self):
        self.assertErrorResponse(
            views.UnsupportedMediaTypeView,
            {
                "code": "unsupported_media_type",
                "title": _('Unsupported media type "{media_type}" in request.'),
                "status": 415,
                "detail": _("This media type is not supported"),
            },
        )

    def test_429_error(self):
        self.assertErrorResponse(
            views.ThrottledView,
            {
                "code": "throttled",
                "title": _("Request was throttled."),
                "status": 429,
                "detail": _("Too many requests"),
            },
        )

    def test_500_error(self):
        self.assertErrorResponse(
            views.InternalServerErrorView,
            {
                "code": "error",
                "title": _("A server error occurred."),
                "status": 500,
                "detail": _("Everything broke"),
            },
        )
