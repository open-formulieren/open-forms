from django.contrib.auth.models import Group, Permission

import factory
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.util import random_hex


class TOTPDeviceFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory("openforms.accounts.tests.factories.UserFactory")
    key = factory.LazyAttribute(lambda o: random_hex())

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = "otp_totp.TOTPDevice"


class RecoveryDeviceFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory("openforms.accounts.tests.factories.UserFactory")
    name = "backup"

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = StaticDevice


class RecoveryTokenFactory(factory.django.DjangoModelFactory):
    device = factory.SubFactory(RecoveryDeviceFactory)
    token = factory.LazyFunction(StaticToken.random_token)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = StaticToken


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"user-{n}")
    password = factory.PostGenerationMethodCall("set_password", "secret")

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = "accounts.User"

    class Params:
        with_totp_device = factory.Trait(
            device=factory.RelatedFactory(
                TOTPDeviceFactory,
                "user",
                name="default",
            )
        )

    @factory.post_generation
    def user_permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for permission in extracted:
                if isinstance(permission, str):
                    try:
                        label, codename = permission.split(".")
                    except ValueError:
                        label = ""
                        codename = permission

                    filters = {"codename": codename}
                    if label:
                        filters["content_type__app_label"] = label

                    permission = Permission.objects.get(**filters)
                self.user_permissions.add(permission)  # pyright: ignore


class StaffUserFactory(UserFactory):
    is_staff = True


class SuperUserFactory(StaffUserFactory):
    is_superuser = True


class TokenFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = "authtoken.Token"


class GroupFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("bs")

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Group

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for permission in extracted:
                if isinstance(permission, str):
                    try:
                        label, codename = permission.split(".")
                    except ValueError:
                        label = ""
                        codename = permission

                    filters = {"codename": codename}
                    if label:
                        filters["content_type__app_label"] = label

                    permission = Permission.objects.get(**filters)
                self.permissions.add(permission)  # pyright: ignore
