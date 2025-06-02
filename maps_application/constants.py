'''constants.py - Constants for the maps application.
Import this as a module.
'''

# PostgreSQL on Grendel
DB_HOST = 'grendel.local'
DB_PORT = '5432'
DB_NAME = 'mapsdb'
DB_USER = 'mapsuser'
DB_PASS = 'Pickering-Darlington-30'
#DB_PASS = ''
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
    "geigiecast-zen:65004x",  # Louis Zen when Nano/Cast 2106 not available
    "geigiecast-zen:65049",
    "geigiecast:62106",
    "geigiecast:63209"
]



if __name__ == '__main__':
    print('Please import this as a module.')
