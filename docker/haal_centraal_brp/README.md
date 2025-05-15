# HaalCentraal BRP (V2)

Open Forms supports the Haal Centraal BRP Personen bevragen API.

We include a compose stack for development and testing/CI purposes, which is part of the official
documentation of the HaalCentraal
(https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/getting-started#probeer-en-test-de-api-lokaal).
This is a service (mock) with test data and it is **NOT** suitable for production usage.

## docker compose

Start a HaalCentraal-BRP instance in your local environment from the parent directory:

```bash
docker compose -f docker-compose.hc-brp-mock.yml up -d
```

## Testing

This brings up the service and you can now make API calls by using
http://localhost:5010/haalcentraal/api/brp/personen. Of course these calls have to be according to
the specification (https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc).

### Test data

Inside the container in `/app/Data/` directory you can find a json file with the initial test data
that the API provides. This file is part of the docker container itself and it can be modified
according to our needs. Trying to put unknown attributes/parameters will work as expected with a
validation error (400).

#### Please make sure you follow the correct steps when adding new/modifying test data:

- copy the _/app/Data/test-data.json_ file into your local machine

  `docker cp <container_id>:/app/Data/test-data.json /desired_path/test-data.json`

- modify the data of the local file according to your needs
- create a patch file (_some-change-bsnNumber.patch_) and save it to open-forms/patches directory by
  using the last commit (with the changes ou made)

  `git format-patch -1`

- copy the new json file into the container

  `docker cp /path/to/test-data.json <container_id>:/app/Data/test-data.json`

- restart the container and you can test your new test cases

#### In case you want to apply a new patch you follow these steps:

- apply the patch to your local json file

  `git am some-change-bsnNumber.patch`

- copy the updated file into the container

  `docker cp /path/to/test-data.json <container_id>:/app/Data/test-data.json `

### Extras

- See https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/fields for building the correct field
  structure (useful for nested fields).
