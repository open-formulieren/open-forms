# Test files for DigiD

## Certificate and key

The test.certificate and the test.key were generated using the following command:

```bash
openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out test.certificate -keyout test.key
```

The tests making use of these certificates are:
- `src/openforms/authentication/contrib/digid/tests/test_auth_procedure.py`
- `src/openforms/authentication/contrib/eherkenning/tests/test_auth.py`

These tests will potentially start failing once the test certificate expires.
