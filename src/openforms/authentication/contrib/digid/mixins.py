from furl import furl


class AssertionConsumerServiceMixin:
    def get_failure_url(self, parameter: str, problem_code: str) -> str:
        url = self.get_success_url()
        f = furl(url)
        f.args[parameter] = problem_code
        return f.url
