#!/bin/bash

# This if statement should only run on the first time the container is spun up
if [ ! -f /.db_created ]; then

    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY=$(tr -dc 'a-f0-9' < /dev/urandom | fold -w 24 | head -n 1)
    fi

    CONFIG_FILE=/etc/anitya/config.toml
    if [ -f "$CONFIG_FILE" ]; then
        echo "Replacing SECRET_KEY with generated value"
        sed -i "s/changeme please/${SECRET_KEY}/g" "$CONFIG_FILE"
    else
        echo "secret_key = '${SECRET_KEY}'" > "$CONFIG_FILE"
    fi

    python3 /app/createdb.py
    touch /.db_created
fi

exec env FLASK_APP=runserver.py flask run --host 0.0.0.0 --port 80
