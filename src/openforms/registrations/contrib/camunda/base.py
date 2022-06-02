from django_camunda.client import Camunda

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models.submission import Submission


class BasePlugin(AbstractBasePlugin):
    def obtain_reference(self, client: Camunda, submission: Submission) -> str:
        """
        Hook to extract a reference from the process according to your business logic.

        Typically you'll want to use submission.registration_result to get the process
        instance ID and perhaps even write to the field with extra meta-information.
        """
        return ""
