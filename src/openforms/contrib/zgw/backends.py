from openforms.contrib.zgw.service import create_document, create_zaak, relate_document
from openforms.core.backends import register


@register
def create_zaak_backend(submission_step) -> dict:
    zaak = create_zaak()
    document = create_document(name=submission_step.submission.form.name, body=submission_step.data)
    relate_document(zaak['url'], document['url'])

    result = {
        "zaak": zaak,
        "document": document,
    }
    return result
