from django.urls import reverse

from ...models import Category


class FormListAjaxMixin:
    def _get_form_changelist(self, query=None, **kwargs):
        """
        Utility to mimick the ajax-loading of form tables per category.
        """
        query = query or {}

        url = reverse("admin:forms_form_changelist")
        # get the server rendered scaffolding
        changelist = self.app.get(url, params=query, **kwargs)

        return self._load_async_category_form_lists(changelist, **kwargs)

    def _load_async_category_form_lists(self, response, query=None, **kwargs):
        url = reverse("admin:forms_form_changelist")
        query = dict(response.request.params)

        # get the ajax call responses
        category_ids = [""] + list(Category.objects.values_list("id", flat=True))
        for category_id in category_ids:
            ajax_response = self.app.get(
                url, params={**query, "_async": 1, "category": category_id}, **kwargs
            )
            if not ajax_response.text.strip():
                continue

            pq = response.pyquery("html")
            rows = ajax_response.pyquery("tbody")
            if not rows:
                continue

            # rewrite the response body with the new HTML as if injected by JS
            pq("table").append(rows.html())
            response.text = pq.html()

        response._forms_indexed = None

        return response
