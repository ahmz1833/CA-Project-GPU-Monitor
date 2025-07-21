#!/bin/sh

# Replace environment variables in the configuration template
envsubst < /etc/alertmanager/alertmanager.yml.template > /tmp/alertmanager.yml

# Start alertmanager with the processed configuration
exec /bin/alertmanager --config.file=/tmp/alertmanager.yml --storage.path=/alertmanager --web.external-url=http://localhost:9093 "$@"
