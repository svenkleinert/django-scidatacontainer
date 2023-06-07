import os
import sys
import django
from django.conf import settings
sys.path.insert(0, os.path.abspath('../..'))

# pass settings into configure
settings.configure(
    INSTALLED_APPS = [
                      'scidatacontainer_db.apps.ScidatacontainerDBConfig',
                      'django.contrib.admin',
                      'django.contrib.auth',
                      'django.contrib.contenttypes',
                      'django.contrib.sessions',
                      'django.contrib.messages',
                      'django.contrib.staticfiles',
                      'guardian',
                      'rest_framework',
                      'knox',
                      'django_filters',
                      ])
django.setup()

from django.db import models
import inspect
from django.utils.html import strip_tags
from django.utils.encoding import force_str

def process_docstring(app, what, name, obj, options, lines):
    # This causes import errors if left outside the function

    # Only look at objects that inherit from Django's base model class
    if inspect.isclass(obj) and issubclass(obj, models.Model):
        # Grab the field list from the meta class
        fields = obj._meta.fields

        for field in fields:
            # Decode and strip any html out of the field's help text
            help_text = strip_tags(force_str(field.help_text))

            # Decode and capitalize the verbose name, for use if there isn't
            # any help text
            verbose_name = force_str(field.verbose_name).capitalize()

            if help_text:
                # Add the model field to the end of the docstring as a param
                # using the help text as the description
                lines.append(u':param %s: %s' % (field.attname, help_text))
            else:
                # Add the model field to the end of the docstring as a param
                # using the verbose name as the description
                lines.append(u':param %s: %s' % (field.attname, verbose_name))

            # Add the field's type to the docstring
            lines.append(u':type %s: %s' % (field.attname, type(field).__name__))

    # Return the extended docstring
    return lines

def setup(app):
    # Register the docstring processor with sphinx
    app.connect('autodoc-process-docstring', process_docstring)

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'django-scidatacontainer'
copyright = '2023, Sven Kleinert, Reinhard Caspary'
author = 'Sven Kleinert, Reinhard Caspary'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
              'sphinx_copybutton',
              'sphinx.ext.autodoc',
              'sphinx.ext.autosummary',
              ]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options= {"collapse_navigation" : False}
