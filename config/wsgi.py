"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# VIRTUALENV_SITE = '/var/www/py3env_www/lib/python3.6/site-packages'
# site.addsitedir(VIRTUALENV_SITE)
# sys.path.append('/var/www/dashcamanalysysweb/')
# print >> sys.stderr, sys.path
# os.environ['DJANGO_SETTINGS_MODULE'] = 'speechaccounts.settings'
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# os.environ['PYTHON_EGG_CACHE'] = '/var/www/.python-eggs'
# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
