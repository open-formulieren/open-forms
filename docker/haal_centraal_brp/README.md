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

Note: before running the related tests in the code, please make sure to apply all patches from
_open-forms/patches/haal_centraal_brp_ to the test data. See below for more detailed instructions on
how to create and apply patches.

### Test data

Inside the container in `/app/Data/` directory you can find a json file with the initial test data
that the API provides. This file is part of the docker container itself and it can be modified
according to our needs by using patches. Trying to put unknown attributes/parameters will work as
expected with a validation error (400).

#### Adding a new patch to modify test data:

- Copy the _/app/Data/test-data.json_ file into your local machine. Ensure it is placed inside a
  folder that is tracked by `git`.

  `docker cp <container_id>:/app/Data/test-data.json /desired_path/test-data.json`

- Make sure you first apply all the available patches until now, that are located in the patches
  folder. See below ("Applying an existing patch") for more details.
- Commit the file to ensure changes are being tracked.
- Modify the data of the local file according to your needs.
- Create a patch file (_some-change-bsnNumber.patch_) and save it to
  _open-forms/patches/haal_centraal_brp_ directory by using the last commit (with the changes you
  made).

  `git diff --no-color > /path/to/open-forms/patches/haal_centraal_brp_/some-change-bsnNumber.patch`

- Copy the new json file into the container.

  `docker cp /desired_path/test-data.json <container_id>:/app/Data/test-data.json`

- Restart the container and you can test your new test cases.

When you are done testing:

- Commit and push the patch file for others to use (if applicable).

#### Applying an existing patch:

- If not done already, copy the _/app/Data/test-data.json_ file into your local machine. This must
  be the initial file, without any changes/patches already applied and inside a directory tracked by
  git.

  `docker cp <container_id>:/app/Data/test-data.json /desired_path/test-data.json`

- Apply the patches to your local json file by running the script with the necessary local directory
  (contains the local json file).

  `./patches/haal_centraal_brp/apply_patch_and_copy.sh /desired_path`

The script should now have applied all patches and copied the updated file into the container.

### Extras

- See https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/fields for building the correct field
  structure (useful for nested fields).
