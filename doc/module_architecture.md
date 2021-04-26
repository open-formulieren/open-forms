# Module architecture

Open Forms is built with a modular architecture.

A number of requirements fit a particular module, which is implemented in a
vendor-agnostic fashion to provide an anti-corruption layer. Within a module, a number
of plugins are available/registered to provide a specific implementation.

## MVP/PvE modules

At this point in time, we recognize the following modules with their plugins:

- Appointments
    - Q-matic
    - Lamson
    - JCC Afspraken
- Registrations
    - StUF-ZS-DMS
    - ZGW API's
    - Objects API
    - File location connection(s)
    - MeldDesk
    - E-mail
- Prefill
    - StUF-BG
    - Haal Centraal Personen
    - NHR
- Payments
    - Ingenico
- Authentication
    - eHerkenning
    - DigiD
    - eIDAS

## Code organization

The code is to be organized in a way such that:

* The module functionality is easily found and called (a clear public Python API)
* Plugins are self-contained and isolated (private API)
* New plugins are easily added
* Code is found where you'd expect it

For that purpose, and following the Zen of Python, the project structure should like
like this:

```
.
├── accounts
├── api
├── appointments
│   ├── contrib
│   │   ├── jcc
│   │   ├── lamson
│   │   └── qmatic
│   └── registry.py
├── auth
│   └── contrib
│       ├── digid
│       ├── eherkenning
│       └── eidas
├── conf
├── forms
├── payments
│   ├── contrib
│   │   └── ingenico
│   └── registry.py
├── prefill
│   ├── contrib
│   │   ├── haalcentraal_brp
│   │   ├── nhr
│   │   └── stuf_bg
│   └── registry.py
├── registrations
│   ├── contrib
│   │   ├── email
│   │   ├── file_locations
│   │   ├── melddesk
│   │   ├── objects_rest
│   │   ├── stuf_zs_dms
│   │   └── zgw_rest
│   └── registry.py
└── submissions

```

That is:

- Every module has its own Python package
- The public API of each module runs through `{module}/registry.py`
- Vendor-specific implementations and/or plugins are kept in the `contrib` sub-package

One alternative was to have a top-level `contrib` package, so that the same vendor can
be organized for different modules, but it's unlikely that these will overlap.

## Example public API

A hypothetical example of how this anti-corruption public Python API could look like,
is for the registration of a form submission:

```py
from openforms.registrations.register import registry


def post(self, request):
    serializer = Serializer(request.data)
    serializer.is_valid(raise_exception=True)

    submission = self.perform_create(serializer)

    registry.store_submission(submission)
    return Response(status=204)
```

It's up to the plugins to implement this, e.g.:

```py
from ..registry import register


@register
def store_submission_zgw(submission: Submission) -> None:
    config = ZGWConfig.get_solo()
    zaaktype = config.zaaktype
    documenttype = config.documenttype

    pdf_data = submission.as_pdf()

    zaken_client = config.zaken_service.build_client()
    documents_client = config.zaken_service.build_client()

    zaak = zaken_client.create("zaak", {"zaaktype": zaaktype})
    document = documents_client.create("enkelvoudiginformatieobject", {"inhoud": pdf_data.read()})
    zaken_client.create("zaakinformatieobject", {"zaak": zaak["url"], "informatieobject": document["url"]})
```
