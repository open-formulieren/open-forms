from django.db import models


class AnalyticsTools(models.TextChoices):

    google_analytics = "google_analytics", "Google Analytics"
    matomo = "matomo", "Matomo"
    piwik = "piwik", "Piwik"
    piwik_pro = "piwik_pro", "Piwik Pro"
    siteimprove = "siteimprove", "Siteimprove"
