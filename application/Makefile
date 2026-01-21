.PHONY: run

run:
	@ echo "This command should not be used in a production environment. OAuth requires an https connection outside of development."
	GATEWAY_HOST="localhost:4000/gateway" AUTHLIB_INSECURE_TRANSPORT=true TEMPLATES_AUTO_RELOAD=true ../venv/bin/flask --debug run --reload --debug

sass:
	cd static/styles/ && sass .

format-js:
	cd static/ && biome format . --write
