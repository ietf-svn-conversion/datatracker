#!/bin/bash

WORKSPACEDIR="/workspace"

service rsyslog start

# fix permissions for npm-related paths
WORKSPACE_UID_GID=$(stat --format="%u:%g" "$WORKSPACEDIR")
chown -R "$WORKSPACE_UID_GID" "$WORKSPACEDIR/.parcel-cache"

# Build node packages that requrie native compilation
echo "Compiling native node packages..."
yarn rebuild

# Generate static assets
echo "Building static assets... (this could take a minute or two)"
yarn build

# Copy config files if needed

if [ ! -f "$WORKSPACEDIR/ietf/settings_local.py" ]; then
    echo "Setting up a default settings_local.py ..."
    cp $WORKSPACEDIR/docker/configs/settings_local.py $WORKSPACEDIR/ietf/settings_local.py
else
    echo "Using existing ietf/settings_local.py file"
    if ! cmp -s $WORKSPACEDIR/docker/configs/settings_local.py $WORKSPACEDIR/ietf/settings_local.py; then
        echo "NOTE: Differences detected compared to docker/configs/settings_local.py!"
        echo "We'll assume you made these deliberately."
    fi
fi

if [ ! -f "$WORKSPACEDIR/ietf/settings_local_debug.py" ]; then
    echo "Setting up a default settings_local_debug.py ..."
    cp $WORKSPACEDIR/docker/configs/settings_local_debug.py $WORKSPACEDIR/ietf/settings_local_debug.py
else
    echo "Using existing ietf/settings_local_debug.py file"
    if ! cmp -s $WORKSPACEDIR/docker/configs/settings_local_debug.py $WORKSPACEDIR/ietf/settings_local_debug.py; then
        echo "NOTE: Differences detected compared to docker/configs/settings_local_debug.py!"
        echo "We'll assume you made these deliberately."
    fi
fi

if [ ! -f "$WORKSPACEDIR/ietf/settings_local_sqlitetest.py" ]; then
    echo "Setting up a default settings_local_sqlitetest.py ..."
    cp $WORKSPACEDIR/docker/configs/settings_local_sqlitetest.py $WORKSPACEDIR/ietf/settings_local_sqlitetest.py
else
    echo "Using existing ietf/settings_local_sqlitetest.py file"
    if ! cmp -s $WORKSPACEDIR/docker/configs/settings_local_sqlitetest.py $WORKSPACEDIR/ietf/settings_local_sqlitetest.py; then
        echo "NOTE: Differences detected compared to docker/configs/settings_local_sqlitetest.py!"
        echo "We'll assume you made these deliberately."
    fi
fi

# Create data directories

echo "Creating data directories..."
chmod +x ./docker/scripts/app-create-dirs.sh
./docker/scripts/app-create-dirs.sh

# Download latest coverage results file

echo "Downloading latest coverage results file..."
curl -fsSL https://github.com/ietf-tools/datatracker/releases/latest/download/coverage.json -o release-coverage.json

# Wait for DB container

if [ -n "$EDITOR_VSCODE" ]; then
    echo "Waiting for DB container to come online ..."
    /usr/local/bin/wait-for localhost:3306 -- echo "DB ready"
fi

# Run memcached

/usr/bin/memcached -u root -d

# Initial checks

echo "Running initial checks..."
/usr/local/bin/python $WORKSPACEDIR/ietf/manage.py check --settings=settings_local
# /usr/local/bin/python $WORKSPACEDIR/ietf/manage.py migrate --settings=settings_local

echo "Done!"

if [ -z "$EDITOR_VSCODE" ]; then
    CODE=0
    python -m smtpd -n -c DebuggingServer localhost:2025 &
    if [ -z "$*" ]; then
        echo
        echo "You can execute arbitrary commands now, e.g.,"
        echo
        echo "    ietf/manage.py check && ietf/manage.py runserver 0.0.0.0:8000"
        echo
        echo "to start a development instance of the Datatracker."
        echo
        bash
    else
        echo "Executing \"$*\" and stopping container."
        echo
        bash -c "$*"
        CODE=$?
    fi
    service rsyslog stop
    exit $CODE
fi
