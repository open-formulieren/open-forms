# Custom nginx image build with otel module enabled. See
# https://nginx.org/en/docs/ngx_otel_module.html
FROM nginx:latest

# There are pre-built Debian packages available.
# NOTE: this may break when nginx upstream image updates to Debian 13+

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg2 ca-certificates lsb-release debian-archive-keyring \
    && curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \
        | tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null \
    && echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
        http://nginx.org/packages/mainline/debian `lsb_release -cs` nginx" \
        | tee /etc/apt/sources.list.d/nginx.list \
    && echo "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" \
        | tee /etc/apt/preferences.d/99nginx \
    && cat /etc/apt/preferences.d/99nginx \
    && apt-get update && apt-get install -y --no-install-recommends nginx-module-otel \
    && apt-get remove --purge --auto-remove -y && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/nginx.list

COPY nginx.conf /etc/nginx/nginx.conf
COPY openforms.conf /etc/nginx/conf.d/default.conf
