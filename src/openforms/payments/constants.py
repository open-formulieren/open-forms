from djchoices import ChoiceItem, DjangoChoices


class PaymentRequestType(DjangoChoices):
    get = ChoiceItem("get")
    post = ChoiceItem("post")


class UserAction(DjangoChoices):
    accept = ChoiceItem("accept")
    exception = ChoiceItem("exception")
    cancel = ChoiceItem("cancel")
    # back = ChoiceItem("back")
    # decline = ChoiceItem("decline")

    unknown = ChoiceItem("unknown")
