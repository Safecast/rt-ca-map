'''constants.py - Constants for the maps application.
Import this as a module.

TODO: Many of these constants could come from the environment.
'''

# PostgreSQL on Grendel
DB_HOST = 'grendel.local'
DB_PORT = '5432'
DB_NAME = 'mapsdb'
DB_USER = 'mapsuser'
DB_PASS = ''
DB_CONNECT = {
    "dbname":DB_NAME,
    "user":DB_USER,
    "password":DB_PASS,
    "host":DB_HOST,
    "port":DB_PORT
}

# TT Server 
# Form the URL as 'https://tt.safecast.org/device/geigiecast:62106'
SAFECAST_API_BASE = "https://tt.safecast.org"

# Initial list of devices to monitor
INITIAL_DEVICE_URNS = [
    "geigiecast-zen:65004",  # Louis Zen when bGeigieCast 2106 not available
    "geigiecast-zen:65049",  # Whitby
#    "geigiecast:62106",  # Louis bGeigieCast out of service
    "geigiecast:63209"  # South Ajax
]



if __name__ == '__main__':
    print('Please import this as a module.')
