FROM python:3.13-slim

RUN apt-get update && apt-get install -y gcc libpq-dev build-essential
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /srv/tornium/

COPY ../application/ ./application/
RUN pip install -r  ./application/requirements.txt

COPY ../commons/ ./commons/
RUN pip install -e ./commons/

COPY ../celery/ ./celery/
RUN pip install -e ./celery/

RUN ls -alh

RUN echo "This Dockerfile should not be used in a production environment. OAuth2 requires an HTTPS connection outside of development."
ENV AUTHLIB_INSECURE_TRANSPORT=true
ENV TEMPLATES_AUTO_RELOAD=true

EXPOSE 5000
WORKDIR application/
CMD ["flask", "run", "--debug", "--reload", "--host=0.0.0.0"]
