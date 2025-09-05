from django.db.models import Model

from ..registry import register


class FeedbackUrlMixin:
    def feedback_url(self, obj: Model | None = None) -> str:
        if not obj:
            return ""
        return register["worldline"].get_webhook_url(None)
