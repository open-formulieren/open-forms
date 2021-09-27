from django.http import HttpResponse
from django.views.generic import View
from django.utils import timezone

from django_yubin.models import QueuedMessage
from django_yubin import settings


class MailHealthCheckView(View):
    def get(self, request, *args, **kwargs):
        oldest, too_old = 0, False
        message = QueuedMessage.objects.order_by('date_queued').first()

        if message:
            # In minutes...
            total_seconds = (timezone.now().astimezone() - message.date_queued.astimezone()).total_seconds()
            oldest = round(total_seconds / 60)
            too_old = oldest > settings.MAILER_HC_QUEUED_LIMIT_OLD

        response = 'oldest_queued_email: {} mins\nemails_queued_too_old: {}'.format(oldest, ('no', 'yes')[too_old])
        return HttpResponse(response, content_type='text/plain')


