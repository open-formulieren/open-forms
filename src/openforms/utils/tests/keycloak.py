"""
Keycloak helpers taken from mozilla-django-oidc-db::tests/utils.py & pytest fixtures.

These help dealing with/stubbing out OpenID Provider configuration.

The Keycloak client ID/secret and URLs are set up for the config in
docker/docker-compose.keycloak.yml. See the README.md in docker/keycloak/ for more
information.
"""

from contextlib import nullcontext

from pyquery import PyQuery as pq
from requests import Session

KEYCLOAK_BASE_URL = "http://localhost:8080/realms/test/protocol/openid-connect"


def keycloak_login(
    login_url: str,
    username: str = "testuser",
    password: str = "testuser",
    host: str = "http://testserver/",
    session: Session | None = None,
) -> str:
    """
    Test helper to perform a keycloak login.

    :param login_url: A login URL for keycloak with all query string parameters. E.g.
        `client.get(reverse("login"))["Location"]`.
    :returns: The redirect URI to consume in the django application, with the ``code``
        ``state`` query parameters. Consume this with ``response = client.get(url)``.
    """
    cm = Session() if session is None else nullcontext(session)
    with cm as session:
        login_page = session.get(login_url)
        assert login_page.status_code == 200

        # process keycloak's login form and submit the username + password to
        # authenticate
        document = pq(login_page.text)
        login_form = document("form#kc-form-login")
        submit_url = login_form.attr("action")
        assert isinstance(submit_url, str)
        login_response = session.post(
            submit_url,
            data={
                "username": username,
                "password": password,
                "credentialId": "",
                "login": "Sign In",
            },
            allow_redirects=False,
        )

        assert login_response.status_code == 302
        assert (redirect_uri := login_response.headers["Location"]).startswith(host)

        return redirect_uri
