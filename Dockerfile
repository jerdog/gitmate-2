FROM python:3-alpine3.6
MAINTAINER Muhammad Kaisar Arkhan <yukinagato@protonmail.com>

ENV USER=gitmate ROOT=/usr/src/app NUM_WORKERS=3 LOG_LEVEL=DEBUG TIMEOUT=30

EXPOSE 8000

WORKDIR $ROOT

RUN addgroup -S $USER && \
    adduser -h $ROOT -G $USER -S $USER

ADD requirements.txt $ROOT/

RUN apk add --no-cache docker postgresql-libs && \
    apk add --no-cache --virtual .build-deps \
        g++ \
        gcc \
        gfortran \
        lapack-dev \
        musl-dev \
        postgresql-dev \
        python3-dev && \
    pip install --no-cache-dir -r $ROOT/requirements.txt && \
    apk del .build-deps

ADD . $ROOT

CMD ["./docker/run.sh"]
