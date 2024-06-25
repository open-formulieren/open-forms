from django.db import models


class AnalyticsTools(models.TextChoices):

    google_analytics = "google_analytics", "Google Analytics"
    matomo = "matomo", "Matomo"
    piwik = "piwik", "Piwik"
    piwik_pro = "piwik_pro", "Piwik Pro"
    piwik_pro_tag_manager = "piwik_pro_tag_manager", "Piwik Pro Tag Manager"
    siteimprove = "siteimprove", "Siteimprove"
    govmetric = "govmetric", "GovMetric"
    expoints = "expoints", "Expoints"
