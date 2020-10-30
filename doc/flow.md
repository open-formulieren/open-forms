# Submission flow

This document describes the flow from a frontend perspective, and the desired endpoints.

## Data model

**Form**

A form is a single form, which consists of multiple steps. It's the top-level resource.
An end-user would typically select a particular form to start or resume filling out.

**Form step**

A single step in a `Form`. A form must have at least one step, and can have multiple
steps. A step connects a `Form` and a `FormDefinition`.

**Form definition**

A form definition is the blueprint of the input fields and their layout. It contains the
information for a frontend to be able to present the inputs to the end user.

**Submission**

Essentially a user-specific instance of `Form` data. A submission is tied to a particular
`Form` and tracks the state/position of that `Form` so that an end-user can save the
data in-between and resume the form.

**Submission step**

Essentially a user-specific instance of a `FormStep`. It contains the step-specific
data.

## Possible flows that the backend should cover

### Selecting a form and starting a "session" to fill it out

In the backend, this means a `Submission` must be created for the selected form.

```http
POST /submissions

{
    "form": "/forms/123"
}
```

Response:

```json
{
    "form": 123,
    "id": "e399d391-c166-47b4-a186-a64c60b2f578",
    "nextStep": "/forms/123/steps/42"
}
```

Side-effect is that the submission ID is stored in the user session:

```py
request.user.session["form-submissions"] = ["e399d391-c166-47b4-a186-a64c60b2f578"]
```

The frontend then loads the step:

```http
GET /forms/123/steps/42
```

User fills out the step data, and submits this, which results in the API call:

```http
PUT /submissions/e399d391-c166-47b4-a186-a64c60b2f578/steps/42

{
    "data": {"foo": "bar"}
}
```

Response:

```json
{
    "id": "13a4cb33-67fd-447f-b258-78961ee43390",
    "nextStep": "/forms/123/steps/69"
}
```

This creates or updates the relevant `SubmissionStep`.

**Notes**

- we validate that the `submissionId` in the URL is in
  `request.user.session["form-submissions"]`
- the `PUT` is to account for a single API call based on data we already have that works
  for both create and update
- we know the submission ID, therefore we know the `Form`. Passing in the step ID
  allows us to resolve an existing `SubmissionStep` record, or create one if needed.


Completing the submission is an explicit action. The last step may or may not be
relevant, or connected with complex logic.

```http
POST /submissions/e399d391-c166-47b4-a186-a64c60b2f578/_complete
```

(response: HTTP 204)

A side effect is that the submission ID should be removed from the user session -
blocking the user from changing a submitted form-session.

### Selecting a form, starting it and suspending it half-way

Essentially the same as the above scenario.

Possibly this should be an explicit action with user-input such as e-mail address to
e-mail a magic link allowing them to resume the submission from another device, e.g.:

```http
POST /submissions/e399d391-c166-47b4-a186-a64c60b2f578/_suspend

{
    "email": "jan.piet@example.com",
    "whatsapp": "0633824473",
    "remark": "ABCDE..."
}
```

### Jumping back/forward to particular steps in the form

The `Form`/`Submission` resource should include the steps URLs in correct order, and
the frontend should use those URLs to load the form definitions. You can extend the API
to include whether the step is reachable from the current step or not, which is tracked
in the `Submission`.

We expose this information through the detail resource of a submission

```http
GET /submissions/e399d391-c166-47b4-a186-a64c60b2f578
```

Response:

```json
{
    "id": "e399d391-c166-47b4-a186-a64c60b2f578",
    "url": "/submissions/e399d391-c166-47b4-a186-a64c60b2f578",
    "form": "/forms/123",
    "steps": [
        {
            "id": 42,
            "url": "/forms/123/steps/42",
            "submissionStep": "/submissions/e399d391-c166-47b4-a186-a64c60b2f578/steps/42",
            "available": true,
            "completed": true,
            "current": false,
            "optional": false,
            "name": "Select product"
        },
        {
            "id": 69,
            "url": "/forms/123/steps/69",
            "submissionStep": "/submissions/e399d391-c166-47b4-a186-a64c60b2f578/steps/69",
            "available": true,
            "completed": true,
            "current": false,
            "optional": false,
            "name": "Product details"
        },
        {
            "id": 420,
            "url": "/forms/123/steps/420",
            "submissionStep": "/submissions/e399d391-c166-47b4-a186-a64c60b2f578/steps/420",
            "available": true,
            "completed": false,
            "current": true,
            "optional": false,
            "name": "Personal details"
        },
        {
            "id": 314,
            "url": "/forms/123/steps/314",
            "submissionStep": "/submissions/e399d391-c166-47b4-a186-a64c60b2f578/steps/314",
            "available": true,
            "completed": false,
            "current": false,
            "optional": true,
            "name": "Appointment to collect"
        },
        {
            "id": 271,
            "url": "/forms/123/steps/271",
            "submissionStep": "/submissions/e399d391-c166-47b4-a186-a64c60b2f578/steps/271",
            "available": false,
            "completed": false,
            "current": false,
            "optional": false,
            "name": "Payment"
        }
    ]
}
```

I'm heavily in doubt if this should be a sub-resource, might just include it as part of
the detail URL of the submission itself.

### Coming back to the UI and resuming an earlier started form

This relies on the session cookie, which holds the submission IDs in the user session.

```http
GET /submissions?completed=false
```

Would retrieve the not-completed submissions, e.g.:

```json
[
    {
        "id": "e399d391-c166-47b4-a186-a64c60b2f578",
        "url": "/submissions/e399d391-c166-47b4-a186-a64c60b2f578",
        "form": "/forms/123",
        "currentStep": "/forms/123/steps/420",
        "createdOn": "2020-10-30T12:38:00+01:00",
        "completedOn": null
    }
]
```

This can be presented in an interface, after which the end-user selects the relevant
submission. Using the submission ID/URL, the relevant form with existing submitted
data can then be loaded, after which you rely on the `PUT /submissions/:uuid/steps/:uuid`
calls to submit/update the data for a step.

### Starting a new session for a form while there already is another session

Possible by doing a new `POST /submissions`. The rest is the same as the first flow.
The important change is that the submission creation/update is not done based on the
`form` ID, as that would limit you to only one (active) submission per form.

## Required endpoints

Summary from the above scenarios

- `GET /forms`
- `GET /forms/:uuid`
- `GET /forms/steps/:uuid`

- `POST /submissions`
- `GET /submissions`
- `GET /submissions/:uuid`
- `GET /submissions/:uuid/steps/:uuid`
- `PUT /submissions/:uuid/steps/:uuid`
- `POST /submissions/:uuid/_suspend`
- `POST /submissions/:uuid/_complete`

## Not part of this API design scope

- versions of forms. Once a form is published, it's immutable, to not affect (pending)
  submissions. This allows the submission data to always be matched to an exact
  version.

- there should be an entry point for the latest and a specific version of a form.

- form designers can "edit" forms, but this will create a new version. See: zaaktypen
  in the Catalogi API.

- we keep the form definitions endpoints that spit out the
  [FormIO](https://github.com/formio/formio.js) for usage in Vanilla renderers.
