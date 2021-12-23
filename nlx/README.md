# NLX support

[NLX][NLX] integration is optional.

This directory contains the docker-compose tooling and instructions on how to enable
NLX on the demo network and connect Open Forms services with it.

Ensure you are in the Open Forms repository `nlx` directory for any steps documented
here:

```bash
cd nlx
```

The workaround included in this directory are
[tracked upstream](https://gitlab.com/commonground/nlx/nlx-try-me/-/issues/2).

## Initializing (first time set-up)

The NLX demo/test stack is set up as a git submodule, which needs to be initialized.

```bash
git submodule update --init  # First time only
````

Then, go back to the `nlx` folder and generate your own local certificates. Follow
the directions presented by the script:

```bash
./obtain-certs.sh
```

**Fixing the permissions**

Private keys need locked-down file permissions. The containers run as `UID: 1001`, which
means this must be owner of the private keys:

If your local user ID is different than `UID: 1001`, then you should fix these
permissions:

```bash
sudo chown 1001 nlx-try-me/pki/certs/management-api.try-me.nlx.local-key.pem
sudo chmod go-rwx nlx-try-me/pki/certs/management-api.try-me.nlx.local-key.pem
```

## Running the NLX stack

Navigate to this (`nlx`) directory and start the components using docker-compose:

```bash
docker-compose up
```

and follow the rest of the guide at the
[upstream documentation](https://docs.nlx.io/try-nlx/docker/getting-up-and-running#start-nlx-using-docker-compose)

* Create local user
* Log in to the management API

Your outway should now be available at http://localhost:8081/ and return a response along
the lines of:

```
nlx outway: invalid /serialNumber/service/ url: valid organization serial numbers : [01632483782218484652, 01634811383832203175, 01636643885025837843, 01637938919941400046, 12345678901234567890, 12345678901234567891]
```

## Inspecting the directory

After obtaining the certificates, we can also inspect the services offered on the
demo directory by running the included python script:

```bash
./main.py
```

Note that this uses the generated organization certificates from the set-up and you
may have to fix the ownership of the key value if your local system user does not have
`UID: 1001`:

```bash
sudo chown $UID ./certs/org.key
```

## Updating the NLX stack

The compose file and related files are obtained from the
[upstream documentation](https://docs.nlx.io/try-nlx/docker/introduction).

[NLX]: https://nlx.io
