INSTALLED_APPS = [
    # Note: contenttypes should be first, see Django ticket #10827
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    # Note: If enabled, at least one Site object is required
    # 'django.contrib.sites',
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # django-admin-index
    "ordered_model",
    "django_admin_index",
    # Optional applications.
    "django.contrib.admin",
    # 'django.contrib.admindocs',
    # 'django.contrib.humanize',
    # 'django.contrib.sitemaps',
    # External applications.
    "axes",
    "hijack",
    "compat",  # Part of hijack
    "hijack_admin",
    "rest_framework",
    "rest_framework.authtoken",
    "digid_eherkenning",
    "solo",
    "zgw_consumers",
    # Project applications.
    "openforms.accounts",
    "openforms.contrib.zgw",
    "openforms.core",
    "openforms.products",
    "openforms.sample_app",
    "openforms.ui",
    "openforms.utils",
    "openforms.submissions",
    "openforms.contrib.brp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.locale.LocaleMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

ZGW_CONSUMERS_CLIENT_CLASS = "zgw_consumers.client.ZGWClient"
