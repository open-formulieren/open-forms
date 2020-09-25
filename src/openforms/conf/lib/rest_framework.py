REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        # TODO: left this in here to not break stuff during hackathon
        'rest_framework.authentication.SessionAuthentication',
    ]
}
