#!/bin/bash
#
# Usage, from the root of the repository:
#
#   ./bin/compilemessages_js.sh
#

SUPPORTED_LOCALES=(
  en
  nl
)

for locale in "${SUPPORTED_LOCALES[@]}"; do
  echo "Compiling messages for locale '$locale'"
  npm run compilemessages -- \
    --ast \
    --out-file "src/openforms/js/compiled-lang/$locale.json" \
    "src/openforms/js/lang/$locale.json" \
    "node_modules/@open-formulieren/*/i18n/messages/$locale.json"
done
