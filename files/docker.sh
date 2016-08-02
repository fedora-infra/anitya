#!/bin/bash
# Remove any remnants of apache if it didn't shut down properly
rm -f /var/run/httpd/httpd.pid

# This if statement should only run on the first time the container is spun up
if [ ! -f /.db_created ]; then

    if [ -z "${DB_URL}" ]; then
        echo 'The DB_URL environment variable was not set. This value is required.'
        exit 1
    fi

    if [ "${SECRET_KEY}" ]; then
        echo "SECRET_KEY = '${SECRET_KEY}'" > /etc/anitya/config.py
    else
        echo "SECRET_KEY = '$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 24 | head -n 1)'" > /etc/anitya/config.py
    fi

    echo "DB_URL = '${DB_URL}'" >> /etc/anitya/config.py
    python /opt/anitya/src/createdb.py
    touch /.db_created
fi

unset DB_URL
exec /usr/sbin/httpd -D FOREGROUND
