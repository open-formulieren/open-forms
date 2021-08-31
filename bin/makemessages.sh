#!/bin/bash
cd src/

# Some constants are generated and can be ignored.

python manage.py makemessages \
--all \
--ignore="test_*" \
--ignore="openforms/api/tests/error_views.py" \
--ignore="openforms/prefill/contrib/haalcentraal/constants.py" \
--ignore="openforms/prefill/contrib/kvk/constants.py" \
--ignore="openforms/registrations/constants.py"

cd ..
