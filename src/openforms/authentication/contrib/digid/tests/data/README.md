# Test files for DigiD

## Certificate and key

The test.certificate and the test.key were generated using the following command:

```bash
openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out test.certificate -keyout test.key
```

The tests making use of these certificates are:

- `src/openforms/authentication/contrib/digid/tests/test_migrations.py`

These tests will potentially start failing once the test certificate expires.

## Signicat integration tests

Three files are relevant:

- `our_certificate.pem`
- `our_keys.pem`
- `signicat_metadata.xml`

The certificate needs to be uploaded Signicate. The metadata is obtained from
https://maykin.pre.ie01.signicat.pro/broker/sp/saml/metadata

Tests making use of these files are:

- `src/openforms/authentication/contrib/digid/tests/test_signicat_integration.py`

**Certificate generation**

Generate a key and certificate using `openssl`:

```bash
openssl req -newkey rsa:4096 -x509 -sha256 -days 1065 -nodes -out our_certificate.pem -keyout our_key.pem
```

Next, navigate to the Signicat interface and upload `our_certificate.pem` for the "Localhost DigiD"
and "Localhost eHerkenning" SP Connections. The old expired certificate(s) can be deleted. These
pages also have the download link for the broker metadata.
