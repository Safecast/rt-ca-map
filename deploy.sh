#!/usr/bin/env bash

cd /home/louis/devel/GitHub/Safecast/rt-ca-map/maps_application
# rsync -av -e ssh *.py *.js *.html ../static/css/*.css \
#   grendel.local:/usr/local/www/rt-ca-map/maps_application/
rsync -av -e ssh --exclude '__pycache__' --exclude 'deploy.sh' \
  . grendel.local:/usr/local/www/rt-ca-map/maps_application/

cd /home/louis/devel/GitHub/Safecast/rt-ca-map/static
rsync -av -e ssh --exclude '__pycache__' --exclude 'misc' --exclude 'radiation-map' \
  . grendel.local:/usr/local/www/rt-ca-map/static/

# To test the application, ssh to the server in that directory
# Activate the venv
# Execute $ uvicorn maps_application.asgi:app 
# Test with curl or httpie to the server from local or the ssh session.


