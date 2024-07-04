---
name: Prepare release
about: Checklist for new releases
title: Prepare release x.y.z
labels: ''
assignees: sergei-maertens
---

- [ ] Resolve release blockers
  - [ ] ...
- [ ] Re-generate VCR cassettes for API tests (see instructions on Taiga). You can find all test
      cases with `grep OFVCRMixin -r src`
  - [ ] Accounts (`openforms.accounts.tests.test_oidc`)
  - Appoinments: Qmatic (`openforms.appointments.contrib.qmatic`) (no testenv available anymore)
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
    - [ ] `soap.tests.test_client`
    - `suwinet.tests.test_client` (testenv access has been retracted and won't be reinstated)
  - [ ] Form imports: `openforms.forms.tests.test_import_export`
  - Payment plugins
    - [ ] Ogone legacy: `openforms.payments.contrib.ogone.tests.test_client`
  - Registration plugins:
    - [ ] Objects API: `openforms.registrations.contrib.objects_api`
    - [ ] ZGW APIs: `openforms.registrations.contrib.zgw_apis`
- [ ] Release new SDK version
- [ ] Correct SDK version pinned in `.sdk-release`
- [ ] Check translations
  - [ ] SDK
  - [ ] Backend
  - [ ] Frontend
  - [ ] Formio
- [ ] Bump API version number
  - [ ] Version bump
  - [ ] Regenerate API spec
  - [ ] Update READMEs with release dates + links
- [ ] Bump version number (including package-lock.json)
- [ ] Update changelog
