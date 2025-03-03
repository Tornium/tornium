.PHONY: run

run:
	TEMPLATES_AUTO_RELOAD=true ../venv/bin/flask --debug run --reload --debug

sass:
	cd static/styles/ && sass .

format-js:
	cd static/ && biome format . --write
