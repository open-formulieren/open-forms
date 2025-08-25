# Keycloak infrastructure

Open Forms supports OpenID Connect as an authentication protocol. Keycloak is an example of an
Identity Provider that supports OIDC.

We include a compose stack for development and testing/CI purposes. This is **NOT** suitable for
production usage.

## docker compose

Start a Keycloak instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.keycloak.yml up -d
```

This brings up Keycloak, the admin interface is accessible at http://localhost:8080/. You can now
log in with the `admin`/`admin` credentials.

In order to allow access to Keycloak via the same hostname via the Open Forms backend container and
the browser, add the following entry to your `/etc/hosts` file:

```
127.0.0.1 keycloak.open-forms.local
```

## Testing

This realm is used in the integration tests. We re-record the network traffic periodically (using
VCR.py). The primary reason this setup exists, is for automated testing reasons.

### Test data

**Clients**

- Client ID: `test-userinfo-jwt`, secret `ktGlGUELd1FR7dTXc84L7dJzUTjCtw9S`

  Configured to return the user info as a JWT rather than JSON response.

- Client ID: `testid`, secret: `7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I`

**Users**

- `testuser` / `testuser`, has the `bsn`, `kvk`, `name_qualifier`, `legalSubjectID` and
  `actingSubjectID` attributes (authentication plugins: DigiD, eHerkenning)
- `digid-machtigen` / `digid-machtigen`, has the `aanvrager.bsn`, `gemachtigde.bsn` and `service_id`
  attributes (for DigiD machtigen)
- `eherkenning-bewindvoering` / `eherkenning-bewindvoering`, has the `legalSubjectID` (kvk),
  `actingSubjectID` (pseudo ID), `representeeBSN`, `service_id`, `service_uuid`, and
  `name_qualifier` attributes (for eHerkenning bewindvoering)
- `eherkenning-vestiging` / `eherkenning-vestiging`, has the `vestiging` attribute plus the
  attributes from `eherkenning-bewindvoering`.
- `admin` / `admin`, intended to create as django user (can be made staff). The email address is
  `admin@example.com`. Should get the `employeeId` claim (See below for how to add the custom
  claim).
- `eidas-person` / `eidas-person`, has the `person_bsn_identifier`, `first_name`, `family_name`,
  `birthdate`, `service_id` and `service_uuid` attributes (for eIDAS with natural person)
- `eidas-person-pseudo` / `eidas-person-pseudo`, has the `person_pseudo_identifier`, `first_name`,
  `family_name`, `birthdate`, `service_id` and `service_uuid` attributes (for eIDAS with natural
  person)
- `eidas-company` / `eidas-company`, has the `person_bsn_identifier`, `company_identifier`,
  `company_identifier_type`, `company_name`, `first_name`, `family_name`, `birthdate`, `service_id`
  and `service_uuid` attributes (for eIDAS with company)
- `eidas-company-pseudo` / `eidas-company-pseudo`, has the `person_bsn_identifier`,
  `company_identifier`, `company_identifier_type`, `company_name`, `first_name`, `family_name`,
  `birthdate`, `service_id` and `service_uuid` attributes (for eIDAS with company)

## Adding a custom claim to Keycloak

\*\*You can copy over the endpoints needed for the Open Forms OpenID Connect configuration by going
to the admin page of Keycloak and on the left side bar (_Realm settings_) you can find the json file
(_OpenID Endpoint Configuration_).

1. Login to the local instance of Keycloak with the credentials mentioned above.
2. Choose user `test` from the left sidebar.
3. Go to the *Client scopes* on the left sidebar and click _Create client scope_
4. Fill in the necessary details (Name is the only one needed - you can turn *Display on consent
   screen* to off)
5. Click Save and on the same form click _Mappers_ > _Configure a new mapper_ > _User attribute_
6. Fill in the following:
   - Name: _employeeId_
   - User Attribute: _employeeId_
   - Token Claim Name: _employeeId_
   - Add to ID token: _on_
   - Add to access token: _on_
   - Add to userinfo: _on_
7. Click Save
8. Go to the _Clients_ > _client ID_ (`testid`) > _Client scopes_ > _Add client scope_
9. From the list you can choose the one you created (`employeeId`) and click Add
10. Go to Users and select the user `admin`
11. In the _Attributes_ tab you can add the new attribute _key='employeeId'_ and a value
12. Click Save

\*\* Finally, in user profile in the admin settings for the OIDC organization add the `employee_id`
mapping (http://localhost:8000/admin/mozilla_django_oidc_db/openidconnectconfig/).

\*\* You can evaluate your configuration in Keycloak (see exactly what data will be sent), by
selecting _Clients_ > _The client ID_ (`testid`) > _Client scopes_ > _Evaluate_ (Evaluate is one of
the sub-tabs of Client scopes) by providing the name of the user.

## Exporting the Realm

In short - exporting through the admin UI (rightfully) obfuscates client secrets and user
credentials. However, for reproducible builds/environments, we want to include this data in the
Realm export.

Ensure the service is up and running through docker-compose.

Ensure that UID `1000` can write to `./keycloak/import/`:

```bash
chmod o+rwx ./keycloak/import/
```

Then open another terminal and run:

```bash
docker compose -f docker-compose.keycloak.yml exec keycloak \
   /opt/keycloak/bin/kc.sh \
   export \
   --file /opt/keycloak/data/import/test-realm.json \
   --realm test
```
