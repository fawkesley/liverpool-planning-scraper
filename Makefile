.PHONY: run
run:
	python -m planningscraper.main

.PHONY: createdb
createdb:
	python -m planningscraper.db
