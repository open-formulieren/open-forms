from djchoices import ChoiceItem, DjangoChoices


class ConflictHandling(DjangoChoices):
    fail = ChoiceItem("fail")
    replace = ChoiceItem("replace")
    rename = ChoiceItem("rename")
