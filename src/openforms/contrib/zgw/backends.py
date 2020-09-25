from openforms.contrib.zgw.service import create_document, create_zaak, relate_document
from openforms.core.backends import register


@register
def create_zaak_backend(submission) -> dict:
    zaak = create_zaak()
    document = create_document(name=submission.form_name, body=submission.data)
    relate_document(zaak['url'], document['url'])

    result = {
        "zaak": zaak,
        "document": document,
    }
    return result
