class APITestAssertions:
    def assertValidationErrorCode(self, response, field: str, code="invalid"):
        response_body = response.json()
        self.assertIn("invalidParams", response_body)
        invalid_params = response_body["invalidParams"]
        relevant_errors = [err for err in invalid_params if err["name"] == field]
        self.assertIn(
            code,
            {err["code"] for err in relevant_errors},
            f"No error with code {code} found in errors: {relevant_errors}.",
        )
