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
  - [ ] Accounts (`openforms.accounts.tests.test_oidc`)
  - Appointments: Qmatic (`openforms.appointments.contrib.qmatic`) (no testenv available anymore)
  - Authentication plugins
    - [ ] DigiD (Signicat): `openforms.authentication.contrib.digid.tests.test_signicat_integration`
    - [ ] eHerkenning
          (Signicat):`openforms.authentication.contrib.eherkenning.tests.test_signicat_integration`
    - [ ] DigiD/EH via OIDC: `openforms.authentication.contrib.digid_eherkenning_oidc`
    - [ ] Org via OIDC: `openforms.authentication.contrib.org_oidc`
    - [ ] `openforms.tests.test_registrator_prefill`
  - General purpose clients
    - [ ] `openforms.contrib.brk`
    - [ ] `openforms.contrib.haal_centraal.tests.test_integration`
    - [ ] `openforms.contrib.kvk`
    - [ ] `openforms.contrib.objects_api.tests`
    - `suwinet.tests.test_client` (testenv access has been retracted and won't be reinstated)
  - Family members
    - [ ] `openforms.prefill.contrib.family_members.tests.test_plugin`
    - [ ] `openforms.emails.tests.test_digest_functions`
  - Forms
    - [ ] `openforms.forms.tests.test_import_export`
    - [ ] `openforms.forms.tests.e2e_tests.test_registration_backend_conf`
    - [ ] `openforms.formio.formatters.tests.test_default_formatters`
  - Payment plugins
    - [ ] Ogone legacy: `openforms.payments.contrib.ogone.tests.test_client`
    - [ ] Worldline: `openforms.payments.contrib.worldline.tests.test_plugin`
  - Prefill
    - [ ] Objects API: `openforms.prefill.contrib.objects_api`
    - Suwinet: `openforms.prefill.contrib.suwinet` (testenv access has been retracted and won't be
      reinstated)
  - ReferenceLists:
    - [ ] `openforms.contrib.reference_lists`
    - [ ] `openforms.emails.tests.test_tasks_integration`
    - [ ] `openforms.formio.dynamic_config.tests.test_reference_lists_config`
    - [ ] `openforms.forms.tests.test_json_schema`
  - Registration plugins:
    - [ ] Objects API: `openforms.registrations.contrib.objects_api`
    - [ ] ZGW APIs: `openforms.registrations.contrib.zgw_apis`
    - [ ] StUF_ZDS APIs: `openforms.registrations.contrib.stuf_zds.tests.test_backend`
    - [ ] Generic JSON: `openforms.registrations.contrib.generic_json.tests.test_backend`
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
