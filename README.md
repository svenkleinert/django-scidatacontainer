# SciDataContainer Django Server

[![Documentation Status](https://readthedocs.org/projects/django-scidatacontainer/badge/?version=latest)](https://django-scidatacontainer.readthedocs.io/en/latest/?badge=latest)

This is the django based implementation of the server to manage [`SciDataContainer`](https://pypi.org/project/scidatacontainer/) objects.

## Documentation

The [`documentation`](https://django-scidatacontainer.readthedocs.io/en/latest/) is hosted on [`Read the Docs`](https://readthedocs.org/).

## Installation

Install using pip:

    pip install django-scidatacontainer

Then add ``'scidatacontainer_db'`` and all third party libraries to your ``INSTALLED_APPS``.

    INSTALLED_APPS = [
        ...,
        'scidatacontainer_db',
        'guardian',
        'rest_framework',
        'knox',
        'django_filters',
    ]

Finally, configure it in your ``settings.py``.
- Define ``MEDIA_ROOT``. It is the location where the dataset files are stored.
- Define `` LOGIN_URL`` and ``LOGOUT_REDIRECT_URL``. This packages provides a login page that can be used.
- Configure the required third party packages.

A good starting point might be the following configuration:

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'guardian.backends.ObjectPermissionBackend',
    )

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'knox.auth.TokenAuthentication',
            # remove the following if you only want to allow token authentification (no web browser)
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated', # only registered user have access.
            # 'rest_framework.permissions.AllowAny', # everyone can access the api.
            ],
        # Make sure datetime is imported!!
        # API key settings: valid for 2 weeks, but the expiration date is extended by 2 weeks every time it's used.
        'TOKEN_TTL' : datetime.timedelta(weeks=2),
        'AUTO_REFRESH' : True,
    }


