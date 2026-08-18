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

This will automatically apply our test-data patches for situations that aren't covered in the
upstream dataset.

## Testing

This brings up the service and you can now make API calls by using
http://localhost:5010/haalcentraal/api/brp/personen. Of course these calls have to be according to
the specification (https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc).

### Test data

Inside the container in `/app/Data/` directory you can find a json file with the initial test data
that the API provides. This file is part of the docker container itself and it can be modified
according to our needs by using patches. Trying to put unknown attributes/parameters will work as
expected with a validation error (400).

#### Adding a new patch to modify test data:

The docker compose setup creates a volume that will have a (modified) copy of the test data, taken
from `/app/Data/test-data.json` inside the container. The volume name ends with `hc-test-data`. You
can list the available volumes with:

```bash
[sudo] docker volume ls
```

Copy this test data to a folder that is tracked by `git`:

```bash
sudo cp /var/lib/docker/volumes/docker_hc-test-data/_data/test-data.json /desired_path/test-data.json
```

- Commit the file to ensure changes are being tracked.
- Modify the data of the local file according to your needs.
- Create a patch file (`XXX-some-change-bsnNumber.patch`) and save it to the
  `open-forms/patches/haal_centraal_brp` directory by using the last commit (with the changes you
  made). Make sure to replace `XXX` with the next number, as the patches need to be applied in the
  right order.

  ```bash
  git diff --no-color > /path/to/open-forms/patches/haal_centraal_brp/XXX-some-change-bsnNumber.patch
  ```

- Copy (and overwrite) the new json file into the volume:

  ```bash
  sudo cp /desired_path/test-data.json /var/lib/docker/volumes/docker_hc-test-data/_data/test-data.json
  ```

- Restart the container and you can test your new test cases.

When you are done testing:

- Commit and push the patch file for others to use (if applicable).

#### Applying an existing patch:

The patches are automatically applied whenever the docker compose service is started.

### Extras

- See https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/fields for building the correct field
  structure (useful for nested fields).
