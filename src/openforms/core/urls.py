from django.urls import path

from .views.FormDefinition import FormDefinitionListView, FormDefinitionDetailView

app_name = 'core'

urlpatterns = [
    path("", FormDefinitionListView.as_view(), name="form_definition_list"),
    path("<slug:slug>", FormDefinitionDetailView.as_view(), name="form_definition_detail")
]
