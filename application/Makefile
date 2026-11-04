.PHONY: run

run:
	@ echo "This command should not be used in a production environment. OAuth requires an https connection outside of development."
	AUTHLIB_INSECURE_TRANSPORT=true TEMPLATES_AUTO_RELOAD=true ../venv/bin/flask --debug run --reload --debug

run-gunicorn:
	@ echo "This command should not be used in a production environment. OAuth requires an https connection outside of development."
	$(eval PROMETHEUS_MULTIPROC_DIR := $(shell mktemp -d))
	AUTHLIB_INSECURE_TRANSPORT=true PROMETHEUS_MULTIPROC_DIR=${PROMETHEUS_MULTIPROC_DIR} gunicorn -c python:gunicorn_hooks --bind 0.0.0.0:8080 --worker-class gthread --workers 4 --threads 4 --log-level debug app:app
	rm -rf $(PROMETHEUS_MULTIPROC_DIR)

sass:
	cd static/styles/ && sass .

format-js:
	cd static/ && biome format . --write
