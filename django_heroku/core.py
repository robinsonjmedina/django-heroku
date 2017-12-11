import logging
import os

import dj_database_url

MAX_CONN_AGE = 600

logger = logging.getLogger(__name__)


def mkdir_p(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError(
            "a file with the same name as the desired "
            "dir, '%s', already exists." % newdir
        )
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir_p(head)

        if tail:
            os.mkdir(newdir)


def settings(config, databases=True, staticfiles=True, allowed_hosts=True, logging=True, secret_key=True):

    # Database configuration.
    # TODO: support other database (e.g. TEAL, AMBER, etc, automatically.)
    if databases:
        # Integrity check.
        if 'DATABASES' not in config:
            config['DATABASES'] = {'default': None}

        # Support all Heroku databases.
        for (env, url) in os.environ.items():
            if env.startswith('HEROKU_POSTGRESQL'):
                db_color = env[len('HEROKU_POSTGRESQL_'):].split('_')[0]

                logger.info('Adding ${} to DATABASES Django setting ({}).'.format(env, db_color))

                config['DATABASES'][db_color] = dj_database_url.parse(url, conn_max_age=MAX_CONN_AGE)

        if 'DATABASE_URL' in os.environ:
            logger.info('Adding $DATABASE_URL to DATABASES Django setting.')

            # Configure Django for DATABASE_URL environment variable.
            config['DATABASES']['default'] = dj_database_url.config(conn_max_age=MAX_CONN_AGE)

        else:
            logger.info('$DATABASE_URL not found, falling back to previous settings!')

    # Staticfiles configuration.
    if staticfiles:
        logger.info('Applying Heroku Staticfiles configuration to Django settings.')

        config['STATIC_ROOT'] = os.path.join(config['BASE_DIR'], 'staticfiles')
        config['STATIC_URL'] = '/static/'

        # Ensure STATIC_ROOT exists.
        mkdir_p(config['STATIC_ROOT'])

        # Insert Whitenoise Middleware.
        try:
            config['MIDDLEWARE_CLASSES'] = tuple(['whitenoise.middleware.WhiteNoiseMiddleware'] + list(config['MIDDLEWARE_CLASSES']))
        except KeyError:
            config['MIDDLEWARE'] = tuple(['whitenoise.middleware.WhiteNoiseMiddleware'] + list(config['MIDDLEWARE']))

        # Enable GZip.
        config['STATICFILES_STORAGE'] = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

    if allowed_hosts:
        logger.info('Applying Heroku ALLOWED_HOSTS configuration to Django settings.')
        config['ALLOWED_HOSTS'] = ['*']

    if logging:
        logger.info('Applying Heroku logging configuration to Django settings.')

        config['LOGGING'] = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                               'pathname=%(pathname)s lineno=%(lineno)s ' +
                               'funcname=%(funcName)s %(message)s'),
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s %(message)s'
                }
            },
            'handlers': {
                'null': {
                    'level': 'DEBUG',
                    'class': 'logging.NullHandler',
                },
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose'
                }
            },
            'loggers': {
                'testlogger': {
                    'handlers': ['console'],
                    'level': 'INFO',
                }
            }
        }

    # SECRET_KEY configuration.
    if secret_key:
        if 'SECRET_KEY' in os.environ:
            logger.info('Adding $SECRET_KEY to SECRET_KEY Django setting.')

