Installation
============

The server is based on `Django <https://www.djangoproject.com/>`_.
So make sure you have `Django installed <https://docs.djangoproject.com/en/4.2/intro/install/>`_ and you
have a `Django project <https://docs.djangoproject.com/en/4.2/intro/tutorial01/>`_ where you can use the app.

Then download the source code or the installation file inside the `dist` folder of the github repository.
You can install it via::

    >>> pip install django-scidatacontainer

Afterwards add this app and all other requirements to your `INSTALLED_APPS` in your `<project-name>/settings.py`::

    INSTALLED_APPS = [...,
                      'scidatacontainer_db',
                      'guardian',
                      'rest_framework',
                      'knox',
                      'django_filters',
                      ]

The configuration of the app happens in the `<project-name>/settings.py`.

* Define `MEDIA_ROOT`. It is the location where the dataset files are stored.
* Define `LOGIN_URL` and `LOGOUT_REDIRECT_URL`. This packages provides a login page that can be used.

Configure of the required third party packages is required, too. A good starting point might be the following configuration::

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

Make sure you import the urls to your project urls. If you want this app to be accessible at the root url, add the following to `<project-name>/urls.py`::

    urlpatterns = [
                   path('', include("scidatacontainer_db.urls")),
                   ...
                   ]
