from django.test import TestCase

import time_machine

from ..models import InitialSubmissionData
from ..tasks import cleanup_expired_initial_data
from .factories import InitialSubmissionDataFactory


class CleanupTaskTests(TestCase):
    def test_cleanup_expired_tasks(self):
        with time_machine.travel("2026-01-31T12:00:00Z"):
            ttl_1_hour = InitialSubmissionDataFactory.create(ttl_hours=1)
            ttl_3_hours = InitialSubmissionDataFactory.create(ttl_hours=3)
            ttl_12_hours = InitialSubmissionDataFactory.create(ttl_hours=12)

        with time_machine.travel("2026-01-31T15:30:00Z"):  # 3.5 hours later
            cleanup_expired_initial_data()

        self.assertFalse(
            InitialSubmissionData.objects.filter(pk=ttl_1_hour.pk).exists()
        )
        self.assertFalse(
            InitialSubmissionData.objects.filter(pk=ttl_3_hours.pk).exists()
        )
        self.assertTrue(
            InitialSubmissionData.objects.filter(pk=ttl_12_hours.pk).exists()
        )
