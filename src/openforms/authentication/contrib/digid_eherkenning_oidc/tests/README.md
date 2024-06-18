# README

The integration tests for the OIDC flavour of DigiD/eHerkenning uses VCR.py. To (re-) record the
cassettes, perform the following steps (from the root of the repo):

1. Bring up the Keycloak instance

   ```bash
   cd docker/
   docker compose -f docker-compose.keycloak.yml up -d
   ```

2. Delete the old cassettes

   ```bash
   rm -rf src/openforms/authentication/contrib/digid_eherkenning_oidc/tests/data/vcr_cassettes
   ```

3. Run the tests

   ```bash
   python src/manage.py test openforms.authentication.contrib.digid_eherkenning_oidc
   ```

4. Inspect the diff and commit the changes.
