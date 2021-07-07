from django.conf import settings

import factory


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"user-{n}")
    password = factory.PostGenerationMethodCall("set_password", "secret")

    class Meta:
        model = "accounts.User"

    @classmethod
    def mock_two_factor_flow(cls, user, app):
        # Mock the user having gone through the two factor authentication flow
        app.set_cookie(settings.SESSION_COOKIE_NAME, "initial")
        session = app.session
        session["otp_device_id"] = user.staticdevice_set.create().persistent_id
        session.save()
        app.set_cookie(settings.SESSION_COOKIE_NAME, session.session_key)

    @classmethod
    def create(cls, **kwargs):
        app = kwargs.pop("app", None)
        user = super().create(**kwargs)

        if app:
            cls.mock_two_factor_flow(user, app)

        return user


class StaffUserFactory(UserFactory):
    is_staff = True


class SuperUserFactory(StaffUserFactory):
    is_superuser = True


class TokenFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = "authtoken.Token"
