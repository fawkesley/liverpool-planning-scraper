.PHONY: run
run:
	python -m planningscraper.main

.PHONY: createdb
createdb:
	python -m planningscraper.db

.PHONY: test
test:
	nosetests -v planningscraper
