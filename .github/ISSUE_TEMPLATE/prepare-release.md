---
name: Prepare release
about: Checklist for new releases
title: Prepare release x.y.z
labels: ''
assignees: sergei-maertens
---

- [ ] Resolve release blockers
  - [ ] ...
- [ ] Re-generate VCR cassettes (delete the old ones and then) for API tests (see instructions on
      Taiga). You can find all test cases with `grep OFVCRMixin -r src`

  - Accounts

    - [ ] `openforms.accounts.tests.test_oidc`

  - Appointments

    - [ ] `openforms.appointments.contrib.jcc_rest.tests.test_plugin`

  - Authentication:

    - [ ] `openforms.authentication.contrib.digid.tests.test_signicat_integration`
    - [ ] `openforms.authentication.contrib.digid_eherkenning_oidc.tests.test_auth_context_data`
    - [ ] `openforms.authentication.contrib.digid_eherkenning_oidc.tests.test_auth_flow_callbacks`
    - [ ] `openforms.authentication.contrib.digid_eherkenning_oidc.tests.test_auth_flow_init`
    - [ ] `openforms.authentication.contrib.digid_eherkenning_oidc.tests.test_auth_flow_logout`
    - [ ] `openforms.authentication.contrib.org_oidc.tests.test_auth_context_data`
    - [ ] `openforms.authentication.contrib.org_oidc.tests.test_auth_flow_callbacks`
    - [ ] `openforms.authentication.contrib.org_oidc.tests.test_auth_flow_init`
    - [ ] `openforms.authentication.contrib.org_oidc.tests.test_auth_flow_logout`
    - [ ] `openforms.authentication.contrib.eherkenning.tests.test_signicat_integration`

  - General purpose clients

    - [ ] `openforms.contrib.brk`
    - [ ] `openforms.contrib.customer_interactions`
    - [ ] `openforms.contrib.haal_centraal.tests.test_integration`
    - [ ] `openforms.contrib.kvk`
    - [ ] `openforms.contrib.objects_api`
    - [ ] `openforms.contrib.reference_lists`

  - Email digest

    - [ ] `openforms.emails.tests.test_digest_functions.FamilyMembersBrokenHCConfigurationTests`
    - [ ] `openforms.emails.tests.test_digest_functions.InvalidMapComponentOverlaysTests`
    - [ ] `openforms.emails.tests.test_tasks_integration.ReferenceListsExpiredDataTests`

  - Formio components

    - [ ] `openforms.formio.dynamic_config.tests.test_reference_lists_config`
    - [ ] `openforms.formio.formatters.tests.test_default_formatters.MapFormatterTests`

  - Forms

    - [ ] `openforms.forms.tests.e2e_tests.test_registration_backend_conf`
    - [ ] `openforms.forms.tests.test_import_export`
    - [ ] `openforms.forms.tests.test_json_schema.GenerateJsonSchemaReferenceListsTests`

  - Payments:

    - [ ] `openforms.payments.contrib.worldline`

  - Prefill:

    - [ ] `openforms.tests.test_registrator_prefill` (uses org OIDC)
    - [ ] `openforms.prefill.contrib.customer_interactions`
    - [ ] `openforms.prefill.contrib.family_members`
    - [ ] `openforms.prefill.contrib.objects_api`

  - Registrations:

    - [ ] `openforms.registrations.contrib.generic_json`
    - [ ] `openforms.registrations.contrib.objects_api`
    - [ ] `openforms.registrations.contrib.stuf_zds`
    - [ ] `openforms.registrations.contrib.zgw_apis`

- [ ] Release new SDK version
- [ ] Correct SDK version pinned in `.sdk-release`
- [ ] Check translations
  - [ ] SDK
  - [ ] Backend
  - [ ] Frontend
  - [ ] Formio
- [ ] Bump API version number
  - [ ] Version bump
  - [ ] Regenerate API spec (`./bin/generate_oas.sh`)
  - [ ] Update `docs/developers/versioning` with release dates + links
- [ ] Update the `upgrade_simulation` CI job matrix
- [ ] Bump version number (including package-lock.json)
- [ ] Update changelog
  - [ ] Document upgrade procedure - mention minimum required current version
  - [ ] Document major features (proze)
  - [ ] Document new features
  - [ ] Document bugfixes
  - [ ] Document project maintenance
