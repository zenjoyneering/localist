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

push:
	./utils/droidxml.py push ${DB_NAME} sample_data/res_astrid
