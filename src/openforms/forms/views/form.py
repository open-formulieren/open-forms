from openforms.ui.views.generic import UIDetailView, UIListView

from ..models import Form


class FormListView(UIListView):
    template_name = "core/views/form/form_list.html"
    queryset = Form.objects.live()


class FormDetailView(UIDetailView):
    template_name = "core/views/form/form_detail.html"
    queryset = Form.objects.live()
