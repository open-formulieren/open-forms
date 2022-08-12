from djchoices import ChoiceItem, DjangoChoices


class AnalyticsTools(DjangoChoices):

    google_analytics = ChoiceItem("google_analytics", label="Google Analytics")
    matomo = ChoiceItem("matomo", label="Matomo")
    piwik = ChoiceItem("piwik", label="Piwik")
    piwik_pro = ChoiceItem("piwik_pro", label="Piwik Pro")
    siteimprove = ChoiceItem("siteimprove", label="Siteimprove")
