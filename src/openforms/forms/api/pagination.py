from rest_framework import pagination


class FormDefinitionPagination(pagination.PageNumberPagination):
    """A page number pagination that will be disabled if the specific query parameter
    for page size is set to 0.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = None

    def get_page_size(self, request) -> int | None:
        if (
            self.page_size_query_param
            and request.query_params.get(self.page_query_param) == 0
        ):
            return None
        return super().get_page_size(request)
