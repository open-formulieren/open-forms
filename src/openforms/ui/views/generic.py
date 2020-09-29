from django.views.generic import DetailView, ListView


class UIViewMixin:
    def get_context_data(self, *args, **kwargs):
        return {
            **super().get_context_data(*args, **kwargs),
            "title": self.get_title(),
        }

    def get_title(self):
        return ""


class UIListView(UIViewMixin, ListView):
    template_name = "ui/views/abstract/list.html"

    def get_title(self):
        queryset = self.get_queryset()
        return queryset.model._meta.verbose_name_plural


class UIDetailView(UIViewMixin, DetailView):
    template_name = "ui/views/abstract/detail.html"

    def get_title(self):
        return self.object
