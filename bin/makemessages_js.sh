#!/bin/bash
#
# Usage, from the root of the repository:
#
#   ./bin/makemessages_js.sh
#

SUPPORTED_LOCALES=(
  en
  nl
)

FIXED_ARGS=(
  'src/openforms/js/**/*.js'
  --id-interpolation-pattern '[sha512:contenthash:base64:6]'
  --format src/openforms/js/i18n-formatter.js
)

for locale in "${SUPPORTED_LOCALES[@]}"; do
  echo "Extracting messages for locale '$locale'"
  npm run makemessages -- \
    "${FIXED_ARGS[@]}" \
    --out-file "src/openforms/js/lang/$locale.json"
done
