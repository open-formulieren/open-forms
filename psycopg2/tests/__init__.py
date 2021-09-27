from django import setup
from django.conf import settings

settings.configure(**{
	'DEBUG': True,
	'DATABASES': {
		'default': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'NAME': 'relativedelta-test',
		},
	},
	'MIDDLEWARE': [
		# TODO: Try to reduce the set of absolutely required middlewares
		'request_id.middleware.RequestIdMiddleware',
		'django.contrib.sessions.middleware.SessionMiddleware',
		'django.contrib.auth.middleware.AuthenticationMiddleware',
	],
	'INSTALLED_APPS': [
		'relativedeltafield',
		'tests.testapp',
	],
	'MIGRATION_MODULES': {
		'testapp': None,
		'relativedeltafield': None,
	},
	'USE_TZ': True,
	#'ROOT_URLCONF': 'tests.testapp.urls',
	'LOGGING': {
		'version': 1,
		'handlers': {
			'console': {
				'level': 'DEBUG',
				'class': 'logging.StreamHandler',
			},
		},
		'loggers': {
			# We override only this one to avoid logspam
			# while running tests.  Django warnings are
			# stil shown.
			'django-relativedelta': {
				'handlers': ['console'],
				'level': 'ERROR',
			},
		}
	}
})

setup()

# Do the dance to ensure the models are synched to the DB.
# This saves us from having to include migrations
from django.core.management.commands.migrate import Command as MigrationCommand
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

# This is oh so hacky....
cmd = MigrationCommand()
cmd.verbosity = 0
connection = connections['default']
executor = MigrationExecutor(connection)
cmd.sync_apps(connection, executor.loader.unmigrated_apps)
