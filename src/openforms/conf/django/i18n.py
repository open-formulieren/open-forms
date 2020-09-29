import os

from openforms.conf.django.dirs import DJANGO_PROJECT_DIR

LANGUAGE_CODE = "nl-nl"
LOCALE_PATHS = (os.path.join(DJANGO_PROJECT_DIR, "conf", "locale"),)
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

