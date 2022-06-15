"""
Implement the Camunda 7.x DMN engine.

This plugin supports fetching and evaluating decision definitions (and their versions)
from the Camunda REST API. Introspection of the DMN XML is also available.

Note that Camunda DMN supports decision definitions containing multiple decision tables
for chained evaluation/input. You can trigger this by evaluating the root table and
passing all the descendant leaf input variables.

.. note:: the end-user is responsible for configuring the correct input variable names
   and correctly processing the output variables. On misconfiguration, Camunda returns
   a HTTP 500 response which will be logged and an empty result will be returned by
   Open Forms.

.. note:: Tested with Camunda 7.16.
"""
