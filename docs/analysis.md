# Analysis of changes required for email verification with Open Klant

## Acceptance criteria

- If an email address has not yet been verified, Open Forms enforces the verification
- It uses the existing email verification flow uses for regular email components
- Upon registration, the verification timestamp is persisted to Open Klant
- The email address may be duplicated. As soon as any is verified, the verification is accepted and
  no new verification is necessary.
- This applies only for logged in users with an existing open klant profile, other flows must always
  verify the email address

## Building blocks in Open Forms

### Backend

- `submissions.EmailVerification` model

  - related to submisssion
  - pointer to the component that requested verification
  - email address to verify & one-time-code
  - verification timestamp

- `prefill.contrib.customer_interactions`:

  - retrieve existing digital addresses for a BSN/KVK (using OK client - does not yet return
    verification timestamp)
  - does not de-duplicate addresses
  - `CommunicationPreferencesView` emits the available communication preferences

- `formio.components.custom.CustomerProfile`
  - runs the `pre_registration_hook`

### Frontend

- renderer: `src/registry/email/verification` components + flows
- SDK: `requestVerificationCode`, `verifyCode` context parameters used by renderer

## Changes necessary

- (+3D) Prefill internal datastructures need to be updated - now a simple list of options is
  displayed, but we also need to extract each address verification status + de-duplicate.

  This can cause breakage with existing submissions that are resumed because the data is still in
  old format (edge case!). Transformation to be done in `CommunicationPreferencesView`? Definitely
  the place to aggregate/de-duplicate addresses.

  This also complicates the validation of the customer profile, as a user is not allowed to proceed
  if the verification wasn't completed yet.

- (+2D) `CustomerProfile.pre_registration_hook` needs to check:

  - authentication status, verification status (in OK) and verification status in OF to set/update
    the verification status of the email address. Must target only the email type.

    Additional complexity because sometimes adding email address with new reference necessary,
    sometimes updating existing.

- (+3D) Update frontend code to hook into the verification code from email component, move email
  verification code into shared location because it's now used by multiple component types. Update
  the verification status detection logic, as it's different for email & customerprofile component.

- Update Open Klant library to set verification status.

-> original estimate 10D, + 8D -> 18D estimate.
