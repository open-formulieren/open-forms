from openforms.core.models import FormDefinition
from openforms.ui.views.generic import UIDetailView, UIListView


class FormDefinitionListView(UIListView):
    model = FormDefinition
    template_name = 'core/views/form_definition/form_definition_list.html'


class FormDefinitionDetailView(UIDetailView):
    model = FormDefinition
    template_name = 'core/views/form_definition/form_definition_detail.html'
