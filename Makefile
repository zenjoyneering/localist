DB_NAME = http://admin:admin@localhost:5984/l10n/
AUTH_DB = http://admin:admin@localhost:5984/_users/

default: refresh

refresh: dropdb service push

service: createdb webapp backend auth

dropdb:
	./couchdb/coucher.py dropdb ${DB_NAME}

createdb:
	./couchdb/coucher.py createdb ${DB_NAME}

webapp:
	./couchdb/coucher.py push couchdb/app ${DB_NAME}

backend:
	./couchdb/coucher.py push couchdb/_design ${DB_NAME}

auth:
	./couchdb/coucher.py push couchdb/auth ${AUTH_DB}

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
