#!/usr/bin/env sh

cd /usr/local/www/rt-ca-map/maps_application
. venv/bin/activate

# No reload, supervisor does that for us
# uvicorn --reload maps.asgi:app
uvicorn maps.asgi:app

