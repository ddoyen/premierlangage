"""
Django settings for serverpl project.

Generated by 'django-admin startproject' using Django 1.10.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os, sys, docker
from datetime import date
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'pl-test.u-pem.fr']


# Application definition

INSTALLED_APPS = [
    'gitload',
    'playexo',
    'classmanagement',
    'sandbox',
    'documentation',
    'markdown_deux',
    'bootstrap3',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_auth_lti',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_auth_lti.middleware_patched.MultiLTILaunchAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 5*365*24*60*60

LOGIN_URL="/playexo/not_authenticated/"

ROOT_URLCONF = 'serverpl.urls'

#Overriding 'messages.ERROR: error' to danger so that it correspond to bootstrap3 alert tag
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [
        ],
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
        
    },

]

WSGI_APPLICATION = 'serverpl.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Update database configuration with $DATABASE_URL.
import dj_database_url
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#Logger information
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.dirname(os.path.abspath(__file__))+'/log/'+date.today().isoformat()+'.log',
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['console','file'],
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins','file','console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['file','console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.template': {
            'handlers': ['file','console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['file','console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_lti.backends.LTIAuthBackend',
)

LTI_OAUTH_CREDENTIALS = {
    'moodle': 'secret',
    'test2': 'moodle'
}

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_ROOT = os.path.join(PROJECT_DIR, 'staticfiles')
STATIC_URL = '/static/'


MEDIA_ROOT = os.path.join(PROJECT_DIR, '../../../../tmp')
MEDIA_URL = '/tmp/'


# python plank packtage dir  
PYSRCDIR = os.path.dirname(PROJECT_DIR + "/../pysrc/")
if not PYSRCDIR in sys.path:
    sys.path.append(PYSRCDIR)

DIRREPO=os.path.join(PROJECT_DIR,'../../../repo')
