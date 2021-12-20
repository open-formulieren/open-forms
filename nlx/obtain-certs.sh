#!/bin/bash
#
# Run this script using:
#
#   ./obtain-certs.sh
#
set -eu -o pipefail

ROOT_CERT=https://certportal.demo.nlx.io/root.crt

# this DNS entry does not exist (yet) as we will not be setting up an inway. The CN
# does not have to resolve for an outway.
COMMON_NAME=inway.example.com

cd certs


if [ -f org.crt ]; then
    echo "Looks like you already set up certificates. If you want to reset your environment, delete certs/org.crt"
    exit 1
fi

echo "Downloading root cert"
wget --quiet $ROOT_CERT -O root.crt

echo "Generating service certificate"
openssl req -utf8 -nodes -sha256 -newkey rsa:4096 \
    -keyout org.key \
    -out org.csr \
    -subj "/C=NL/ST=Noord-Holland/L=Amsterdam/O=Open-Forms/OU=OF/CN=${COMMON_NAME}"

echo ""
cat org.csr
echo ""

echo "Private key and CSR generated. Please open https://certportal.demo.nlx.io/ and paste the above CSR contents."
echo ""

echo "Once done, save the certificate in 'certs/org.crt'"
echo ""

read  -n 1 -p "Hit any key to continue:"

while [ ! -f org.crt ]
do
    echo "Could not find 'org.crt' - please save the certificate under this filename."
    read  -n 1 -p "Hit any key to continue:"
done

echo "Attempting to fix/set the correct private key owner..."
chown 1000 org.key

echo "Found your certificate!"
