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

  - [ ] Appoinments: Qmatic
  - [ ] Suwinet
  - DigiD/eHerkenning (Signicat)

    - [ ] `openforms.authentication.contrib.digid.tests.test_signicat_integration`
    - [ ] `openforms.authentication.contrib.eherkenning.tests.test_signicat_integration`

  - OIDC based authentication flows

    - [ ] `openforms.authentication.tests.test_oidc`
    - [ ] `openforms.authentication.contrib.digid_eherkenning_oidc`
    - [ ] `openforms.authentication.contrib.org_oidc`
    - [ ] `openforms.authentication.contrib.org_oidc`
    - [ ] `openforms.tests.test_registrator_prefill`

  - [ ] Haal Centraal BRP Personen bevragen
  - [ ] `soap.tests.test_client`
  - [ ] BRK (Kadaster)
  - [ ] KVK
  - [ ] Ogone
  - [ ] Objects API (registration)
  - [ ] ZGW APIs (registration)
  - [ ] Form imports (registration)

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
