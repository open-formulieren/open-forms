#!/bin/bash
#
# Dump the instance/runtime configuration.
#
# The resulting dump can be restored using the `loaddata` management command. The
# certificate files (certificates + private keys) are dumped into a zip file.
#
# Usage:
#
#   ./bin/dump_configuration.sh
#
# The files will be written to a temporary directory - the script emits the location of
# that directory. You can customize where the directory will be created through the
# `$TMPDIR` environment variable (defaults to /tmp).
#
# Run this from the root of the project.

output_dir=`mktemp -d`

# Dump the certificates to file
OTEL_SDK_DISABLED=True src/manage.py dump_certs --filename "$output_dir/certificates.zip"

# Dump the DB content in a fixture file
OTEL_SDK_DISABLED=True src/manage.py dumpdata \
    --indent=4 \
    --natural-foreign \
    --natural-primary \
    -o "$output_dir/config.json" \
    cookie_consent.CookieGroup \
    cookie_consent.Cookie \
    zgw_consumers \
    config \
    django_camunda.CamundaConfig \
    stuf.SoapService \
    stuf.StufService \
    stuf_bg.StufBGConfig \
    stuf_zds.StufZDSConfig \
    appointments.AppointmentsConfig \
    jcc.JccConfig \
    qmatic.QmaticConfig \
    mozilla_django_oidc_db \
    digid_eherkenning_oidc_generics \
    multidomain \
    bag \
    brp \
    kvk \
    microsoft \
    registrations_microsoft_graph \
    registrations_objects_api \
    zgw_apis \
    prefill \
    prefill_haalcentraal \
    payments_ogone
    # rest_framework.authtoken -> requires users \

echo "The configuration dump can be found in: $output_dir"
