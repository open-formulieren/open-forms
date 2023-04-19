# This is a multi-stage build file, which means a stage is used to build
# the backend (dependencies), the frontend stack and a final production
# stage re-using assets from the build stages. This keeps the final production
# image minimal in size.

# must be at the top to use it in FROM clauses
ARG SDK_RELEASE=latest
FROM openformulieren/open-forms-sdk:${SDK_RELEASE} as sdk-image

# Stage 1 - Backend build environment
# includes compilers and build tooling to create the environment
FROM python:3.10.9-slim-bullseye AS backend-build

RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config \
        build-essential \
        python3-dev \
        libpq-dev \
        libxml2-dev \
        libxslt-dev \
        libxmlsec1-dev \
        zlib1g-dev \
        libxmlsec1-openssl \
        # weasyprint deps
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

        # build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi


WORKDIR /app

# Ensure we use the latest version of pip
RUN pip install pip -U
COPY ./requirements /app/requirements

ARG TARGET_ENVIRONMENT=production
RUN pip install -r requirements/${TARGET_ENVIRONMENT}.txt

# Stage 2 - Install frontend deps and build assets
FROM node:16-bullseye-slim AS frontend-build

WORKDIR /app

# copy configuration/build files
COPY ./build /app/build/
COPY ./*.json ./*.js ./.babelrc /app/

# install WITH dev tooling
RUN npm ci --legacy-peer-deps

# copy source code
COPY ./src /app/src

# build frontend
RUN npm run build

# Stage 3 - Build docker image suitable for production
FROM python:3.10.9-slim-bullseye

# Stage 3.1 - Set up the needed production dependencies
# install all the dependencies for GeoDjango
RUN apt-get update && apt-get install -y --no-install-recommends \
        procps \
        vim \
        mime-support \
        postgresql-client \
        libmagic1 \
        libxmlsec1 \
        libxmlsec1-openssl \
        gettext \
        # lxml deps
        # libxslt \
        # weasyprint deps
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./bin/docker_start.sh /start.sh
COPY ./bin/celery_worker.sh /celery_worker.sh
COPY ./bin/celery_beat.sh /celery_beat.sh
COPY ./bin/celery_flower.sh /celery_flower.sh
COPY ./bin/dump_configuration.sh /dump_configuration.sh
RUN mkdir /app/bin /app/log /app/media /app/private_media /app/certifi_ca_bundle /app/tmp
COPY ./bin/celery_test_worker.py ./bin/celery_test_worker.py

# prevent writing to the container layer, which would degrade performance.
# This also serves as a hint for the intended volumes.
VOLUME ["/app/log", "/app/media", "/app/private_media", "/app/certifi_ca_bundle", /app/tmp]

# copy backend build deps
COPY --from=backend-build /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=backend-build /usr/local/bin/uwsgi /usr/local/bin/uwsgi
COPY --from=backend-build /usr/local/bin/celery /usr/local/bin/celery

# copy frontend build statics
COPY --from=frontend-build /app/src/openforms/static /app/src/openforms/static
COPY --from=frontend-build /app/node_modules/@fortawesome/fontawesome-free/webfonts /app/node_modules/@fortawesome/fontawesome-free/webfonts

# Include SDK files. Collectstatic produces both the versions with and without hash
# in the STATICFILES_ROOT
COPY --from=sdk-image /sdk /app/src/openforms/static/sdk

# copy source code
COPY ./src /app/src
COPY ./.sdk-release /app/.sdk-release

RUN useradd -M -u 1000 maykin
RUN chown -R maykin /app

# drop privileges
USER maykin

ARG RELEASE ARG SDK_RELEASE=latest COMMIT_HASH
ENV GIT_SHA=${COMMIT_HASH}
ENV RELEASE=${RELEASE} SDK_RELEASE=${SDK_RELEASE}

ENV DJANGO_SETTINGS_MODULE=openforms.conf.docker

ARG EXTENSIONS=''
ENV OPEN_FORMS_EXTENSIONS=${EXTENSIONS}

ARG SECRET_KEY=dummy

LABEL org.label-schema.vcs-ref=$COMMIT_HASH \
      org.label-schema.vcs-url="https://github.com/open-formulieren/open-forms" \
      org.label-schema.version=$RELEASE \
      org.label-schema.name="Open Forms"

# Run collectstatic and compilemessages, so the result is already included in
# the image
RUN python src/manage.py collectstatic --noinput \
    && python src/manage.py compilemessages

EXPOSE 8000
CMD ["/start.sh"]
