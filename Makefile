DB_NAME = http://admin:admin@localhost:5984/l10n/

default: refresh

refresh: dropdb createdb webapp backend push

dropdb:
	./couchdb/coucher.py dropdb ${DB_NAME}

createdb:
	./couchdb/coucher.py createdb ${DB_NAME}

webapp:
	./couchdb/coucher.py push couchdb/app ${DB_NAME}

backend:
	./couchdb/coucher.py push couchdb/_design ${DB_NAME}

push: topface meow astrid k9

meow:
	cd sample_data/meow-android && localist push

astrid:
	cd sample_data/astrid && localist push

k9:
	cd sample_data/k-9 && localist push

topface:
	cd sample_data/tf && localist push

test:
	venv/bin/python /usr/bin/nosetests --with-coverage --cover-package=localist tests
