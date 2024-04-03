# Form embedding cases

The JS SDK is built to support embedding forms in third party pages, like CMS pages.

The files here and the `docker compose` configuration in the parent folder (
`docker-compose.embedding.yml`) exist to test and demo this behaviour.

## Requirements

To succesfully run an embed test setup, you need:

- `docker compose`
- an Open Forms 2.5.0+ instance, available over HTTPS. E.g. `https://openforms.example.com`
  - the instance must allow CORS requests from `https://localhost:9000`
  - the instance must have `localhost:9000` in the CSRF trusted origins
- the UUID or the slug of a test form in the above instance, e.g. `my-test-form`

Consult the installation/configuration
[documentation](https://open-forms.readthedocs.io/en/stable/developers/sdk/embedding.html#backend-configuration)
on how to properly configure your backend for embedding.

## Bring up docker compose

All instructions are relative to the top-level directory.

1. Configure the environment by creating or modifying the `.env` file:

   ```bash
   vim ./docker/.env
   ```

   and specify the host of the backend instance:

   ```
   OPENFORMS_HOST=https://openforms.example.com
   ```

2. Then, bring up the docker services:

   ```bash
   docker compose -f ./docker/docker-compose.embedding.yml up
   ```

## Embed test cases

**Query string parameters**

Navigate to `https://localhost:9000/embedding/query-params.html?form=<your-test-form-identifier>`,
where you replace `<your-test-form-identifier>` with the ID or slug of the test form in your
instance.

You will need to accept the self-signed certificates to proceed.

This case demonstrates that a CMS page can dynamically grab the Form ID from the URL/ querystring
and load that form, with hash-based client-side routing.
