# Cypress integration tests

These integration tests are designed to function with a running docker-compose
setup. Start the containers before trying to run the tests:

```bash
$ docker-compose up
```

# Fixtures

The fixtures are present in `cypress/data_fixtures` and can be loaded using this command:

```bash
$ bin/load_ci_fixtures.sh <container_name>
```

Where `<container_name>` is the name of the running Open Forms web container

# Running the tests

To open the Cypress GUI, use the following command:

```bash
$ node_modules/.bin/cypress open
```

This will show a list of all the test files, which can be ran by clicking on them.

To simply run all tests without a GUI, use the following command:

```bash
$ node_modules/.bin/cypress run
```
