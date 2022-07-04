import factory


class FormLogicFactory(factory.django.DjangoModelFactory):
    json_logic_trigger = {"==": [{"var": "test-key"}, 1]}
    actions = [{"action": {"type": "disable-next"}, "component": "testComponent"}]

    class Meta:
        model = "forms.FormLogic"
