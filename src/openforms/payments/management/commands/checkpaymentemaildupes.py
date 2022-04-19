from collections import defaultdict
from uuid import uuid4

from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from django_yubin.models import Message


def get_search_terms():
    left_split = str(uuid4())
    right_split = str(uuid4())
    subject = _(
        "[Open Forms] {form_name} - submission payment received {public_reference}"
    ).format(
        form_name=left_split,
        public_reference=right_split,
    )
    center = subject.split(left_split, maxsplit=1)[1].split(right_split, maxsplit=1)[0]
    start = subject.split(left_split, maxsplit=1)[0]
    return start, center


class Command(BaseCommand):
    help = "Find duplicate payment mails"

    def handle(self, **options):
        start, center = get_search_terms()
        messages = Message.objects.filter(
            subject__startswith=start, subject__contains=center
        )

        counter = defaultdict(list)
        for m in messages:
            counter[m.subject].append(m)

        for key in list(counter.keys()):
            if len(counter[key]) <= 1:
                del counter[key]

        if not counter:
            print("no duplicates")
        else:
            for subject, messages in counter.items():
                count = len(messages)
                ids = ", ".join(f"#{m.id}" for m in messages)
                m = messages[0]
                print(count, m.subject, m.date_created, ids)
