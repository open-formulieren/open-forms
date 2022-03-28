# Notes setting up Camunda DMN

## DMN table

**Input `prApproved`**

Possible values: `true`, `false` (boolean)

**Input `buildPassing`**

Possible values: `true`, `false` (boolean)

**Output `mergeAllowed`**

`true` if both `prApproved` and `buildPassing` are true, otherwise `false`.

## Evaluate

API call on docker-compose instance:

```http
POST /engine-rest/decision-definition/key/dev/evaluate HTTP/1.1
Host: localhost:8080
Authorization: Basic ZGVtbzpkZW1v
Content-Type: application/json
Content-Length: 213

{
    "variables": {
        "prApproved": {
            "type": "boolean",
            "value": true
        },
        "buildPassing": {
            "type": "boolean",
            "value": true
        }
    }
}
```

Response:

```json
[
    {
        "mergeAllowed": {
            "type": "Boolean",
            "value": true,
            "valueInfo": {}
        }
    }
]
```
