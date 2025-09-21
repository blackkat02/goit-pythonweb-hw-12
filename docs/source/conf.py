# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
from unittest.mock import MagicMock
sys.path.insert(0, os.path.abspath('../..'))

# Створюємо заглушку для модуля src.settings
class MockSettings(MagicMock):
    DB_USER = 'dummy'
    DB_PASS = 'dummy'
    DB_NAME = 'dummy'
    DB_HOST = 'dummy'
    DB_PORT = '5432'
    SECRET_KEY = 'dummy_secret'
    MAIL_USERNAME = 'dummy@example.com'
    MAIL_PASSWORD = 'dummy_pass'
    MAIL_FROM = 'dummy@example.com'
    MAIL_FROM_NAME = 'Dummy User'
    MAIL_PORT = '587'
    MAIL_SERVER = 'smtp.dummy.com'
    CLD_NAME = 'dummy_cld'
    CLD_API_KEY = '12345'
    CLD_API_SECRET = 'abcde'

# Підміняємо оригінальний модуль 'src.settings' нашим Mock-об'єктом
sys.modules['src.settings'] = MockSettings()


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'goit-pythonweb-hw-12'
copyright = '2025'
author = 'Boichenko Borys'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
