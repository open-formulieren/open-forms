#!/usr/bin/env python
"""
Debug script to consume the NLX directory API.
"""
import json
import os
from itertools import groupby

import requests

CERTS_DIR = os.path.abspath("certs")

DIRECTORY_ADDRESS = "https://directory-api.demo.nlx.io:443"


def main():
    # get mTLS parameters
    root_cert = os.path.join(CERTS_DIR, "root.crt")
    tls_key = os.path.join(CERTS_DIR, "org.key")
    tls_crt = os.path.join(CERTS_DIR, "org.crt")

    with requests.Session() as session:
        print("Downloading API spec...")
        api_spec_response = session.get(
            f"{DIRECTORY_ADDRESS}/api/swagger.json",
            cert=(tls_crt, tls_key),
            verify=root_cert,
        )
        api_spec_response.raise_for_status()
        with open("directory-api.swagger.json", "w") as outfile:
            json.dump(api_spec_response.json(), outfile, indent=4)

        print("Listing services...")
        service_list_response = session.get(
            f"{DIRECTORY_ADDRESS}/api/directory/list-services"
        )
        service_list_response.raise_for_status()
        services = service_list_response.json()["services"]

        sorted_services = sorted(
            services, key=lambda s: (s["organization"]["serial_number"], s["name"])
        )
        for org, service_list in groupby(
            sorted_services, key=lambda s: s["organization"]
        ):
            print(f"*  Organization: {org['name']} ({org['serial_number']})")
            for service in service_list:
                print(
                    f"  -  {service['name']} (url: 'http://OUTWAY/{org['serial_number']}/{service['name']}/')"
                )


if __name__ == "__main__":
    main()
