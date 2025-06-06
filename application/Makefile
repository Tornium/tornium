.PHONY: run

run:
	@ echo "This command should not be used in a production environment. OAuth requires an https connection outside of development."
	AUTHLIB_INSECURE_TRANSPORT=true TEMPLATES_AUTO_RELOAD=true ../venv/bin/flask --debug run --reload --debug

sass:
	cd static/styles/ && sass .

format-js:
	cd static/ && biome format . --write
