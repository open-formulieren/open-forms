"""
Camunda registration backend.

The camunda registration backend starts a process instance upon completion of a
submission. The process instance ID is stored as a result. (A subset of) Form fields are
included as process instance variables, and derived process variables are possible
to.

The form designer can select which Camunda process definition (including version) to
start for a given form.

Developers can start a local Camunda instance with docker-compose, see the
``docker/camunda/README.md`` file from the root of the repository.
"""
