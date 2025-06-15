#!/usr/bin/env sh
# Create mapsdb and initialize the tables

SU=louis  # Superuser established as installation time.
BIN=/usr/local/bin
WORKDIR=`pwd`

$BIN/createdb --username=$SU --echo --owner=mapsuser mapsdb  "Realtime Maps Database"

# List databases to check the ownership
$BIN/psql --list

# Create the tables in the database 
$BIN/psql --echo-queries --file="postgresql-schema.sql" mapsdb $SU

# Initialize data in the tables based on list from constants.py
$BIN/python3 ../maps_application/bootstrap.py

