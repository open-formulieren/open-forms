"""
Utility to interact with the celery task status.
"""
from dataclasses import dataclass

from django.urls import reverse

from .models import Submission
from .tokens import token_generator


@dataclass
class SubmissionProcessingStatus:
    submission: Submission
