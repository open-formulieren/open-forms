from furl import furl


class AssertionConsumerServiceMixin:
    def get_failure_url(self, parameter: str, problem_code: str) -> str:
        # The success URL is composed by the DigiD plugin endpoint + a 'next' query parameter with the form URL
        url = self.get_success_url()  # type: ignore
        success_url = furl(url)
        form_url = furl(success_url.args.popvalue("next"))  # type: ignore
        form_url.args[parameter] = problem_code
        success_url.args["next"] = form_url.url
        return success_url.url
