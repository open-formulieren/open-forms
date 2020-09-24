from openforms.core.models import Form
from openforms.ui.views.generic import UIDetailView, UIListView


class FormListView(UIListView):
    model = Form
    template_name = 'core/views/form/form_list.html'


class FormDetailView(UIDetailView):
    model = Form
    template_name = 'core/views/form/form_detail.html'
