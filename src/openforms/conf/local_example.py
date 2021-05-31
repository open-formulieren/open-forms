#
# Any machine specific settings when using development settings.
#

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "openforms",
        "USER": "openforms",
        "PASSWORD": "openforms",
        "HOST": "",  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        "PORT": "",  # Set to empty string for default.
    }
}

# allow SPA dev server and API on different ports
CORS_ALLOW_ALL_ORIGINS = True

# run celery tasks so submissions get processed in dev server
CELERY_TASK_ALWAYS_EAGER = True
