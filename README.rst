===================================
SIDER 2 import tool
===================================

Setup
------------

Setup an virtual environment with the required package in the local
directory.

	$ virtualenv --distribute env
	$ . env/bin/activate
	$ pip install -r requirements.txt

Follow the steps...

	$ ./manage.py syncdb

And... start the importing action

	$ DJANGO_SETTINGS_MODULE=settings ./import_sideeffects.py

