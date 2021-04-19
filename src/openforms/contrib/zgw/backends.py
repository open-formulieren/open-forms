from openforms.forms.backends import register

from .service import create_document, create_zaak, relate_document


@register
def create_zaak_backend(submission) -> dict:
    form_config = None

    assert hasattr(submission.form, "zgwformconfig"), "Form should have ZGW config"
    form_config = submission.form.zgwformconfig

    data = {}
    for step in submission.steps:
        data.update(step.data)

    zaak = create_zaak(form_config)
    document = create_document(
        name=submission.form.name, body=data, form_config=form_config
    )
    relate_document(zaak["url"], document["url"])

    result = {
        "zaak": zaak,
        "document": document,
    }
    return result
