# Camunda infrastructure

Open Forms supports Camunda as registration backend, where a completed submission
starts a certain Camunda process.

We include a compose stack for development and CI purposes. This is **NOT** suitable
for production usage.

## docker-compose

Start a Camunda instance in your local environment from the parent directory:

```bash
docker-compse -f docker-compose.camunda.yml up -d
```

This brings up the database and Camunda stack. The Camunda cockpit is accessible on
http://localhost:8080/camunda/. You can log in with `demo:demo`.

## Process models

The sample application contains a demo invoice process model and should be sufficient
to get started.

**Custom process models**

Using the [camunda modeller](https://docs.camunda.org/get-started/quick-start/install/#camunda-modeler)
you can create and deploy BPMN process models.
