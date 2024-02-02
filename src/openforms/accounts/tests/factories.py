from django.contrib.auth.models import Group, Permission

import factory


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"user-{n}")
    password = factory.PostGenerationMethodCall("set_password", "secret")

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
                self.user_permissions.add(permission)

    class Meta:
        model = "accounts.User"


class StaffUserFactory(UserFactory):
    is_staff = True


class SuperUserFactory(StaffUserFactory):
    is_superuser = True


class TokenFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = "authtoken.Token"


class GroupFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("bs")

    class Meta:
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
                self.permissions.add(permission)
