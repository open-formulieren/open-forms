# Test files for EHerkenning

## Certificate and key

The test.certificate and the test.key were generated using the following command:

```bash
openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out test.certificate -keyout test.key
```

The tests making use of these certificates are:

- `src/openforms/authentication/contrib/eherkenning/tests/test_migrations.py`

These tests will potentially start failing once the test certificate expires.

## Signicat integration tests

The setup is the same `openforms.authentication.contrib.digid` - the same certificate, key and
broker metadata are used. The files here are just symlinks to those files.

Tests making use of these files are:

- `src/openforms/authentication/contrib/eherkenning/tests/test_signicat_integration.py`
