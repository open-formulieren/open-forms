---
name: Prepare release
about: Checklist for new releases
title: Prepare release x.y.z
labels: ''
assignees: sergei-maertens
---

- [ ] Resolve release blockers
  - [ ] ...
- [ ] Re-generate VCR cassettes for API tests (see instructions on Taiga)
  - [ ] Appoinments: Qmatic
  - [ ] Suwinet
  - [ ] DigiD/eHerkenning (Signicat)
  - [ ] Haal Centraal BRP Personen bevragen
  - [ ] `src.soap.tests.test_client`
  - [ ] BRK (Kadaster)
  - [ ] KVK
  - [ ] Ogone
  - [ ] Objects API (registration)
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
