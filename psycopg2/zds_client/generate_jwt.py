#!/usr/bin/env python
import argparse

from zds_client import ClientAuth


def _setup_parser():
    parser = argparse.ArgumentParser(
        description="Generate a JWT for a set of credentials"
    )
    parser.add_argument("--client-id", help="Client ID to authenticate with")
    parser.add_argument("--secret", help="Secret belonging to the Client ID")

    # we can accept arbitrary extra arguments/claims in a hackish way, see:
    # https://stackoverflow.com/a/37367814
    parsed, unknown = parser.parse_known_args()  # this is an 'internal' method
    # which returns 'parsed', the same as what parse_args() would return
    # and 'unknown', the remainder of that
    # the difference to parse_args() is that it does not exit when it finds redundant arguments

    parser._extras = []
    for arg in unknown:
        if arg.startswith(("-", "--")):
            # you can pass any arguments to add_argument
            arg_name = arg.split("=")[0]
            parser.add_argument(arg_name, type=str)
            parser._extras.append(arg_name.replace("-", "", 2))

    return parser


def main():
    parser = _setup_parser()
    args = parser.parse_args()

    client_id = args.client_id
    if client_id is None:
        client_id = input("Client ID: ")
    secret = args.secret
    if secret is None:
        secret = input("Secret: ")

    extra_claims = {name: getattr(args, name) for name in parser._extras}

    auth = ClientAuth(client_id, secret, **extra_claims)
    creds = auth.credentials()

    print("Use the following header(s) for authorization:")
    for key, value in creds.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
