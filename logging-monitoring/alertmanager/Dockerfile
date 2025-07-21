FROM alpine:latest as envsubst
RUN apk add --no-cache gettext

FROM prom/alertmanager:latest

USER root

# Copy envsubst and its dependencies from alpine
COPY --from=envsubst /usr/bin/envsubst /usr/bin/envsubst
COPY --from=envsubst /lib/ld-musl-x86_64.so.1 /lib/ld-musl-x86_64.so.1
COPY --from=envsubst /usr/lib/libintl.so.8 /usr/lib/libintl.so.8

# Copy the entrypoint script with execute permissions
COPY --chmod=755 entrypoint.sh /entrypoint.sh

# Copy the config template
COPY alertmanager.yml /etc/alertmanager/alertmanager.yml.template

# Switch back to the default user (nobody)
USER 65534

ENTRYPOINT ["/entrypoint.sh"]
