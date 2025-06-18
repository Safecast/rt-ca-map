'''pgsql_testing.py - Various tests with psycopg and PostgreSQL
'''
import psycopg
from psycopg.rows import dict_row
import json


# PostgreSQL on Grendel
DB_HOST = 'grendel.local'
DB_PORT = '5432'
DB_NAME = 'mapsdb'
DB_USER = 'mapsuser'
DB_PASS = 'Pickering-Darlington-30'
DB_CONNECT = {
    "dbname":DB_NAME,
    "user":DB_USER,
    "password":DB_PASS,
    "host":DB_HOST,
    "port":DB_PORT
}

def get_device_measurement_history(conn, urn: str, days: int = 1) -> list:
    '''Return a list of dict of historical readings for a single device,
    with each entry in the list as a dict, for example
            when_captured: timestamp with time zone
            lnd_7318u: integer as a float
    '''
    curs = conn.cursor()
    curs.execute("""
        SELECT devices.urn as device_urn, 
                to_char(measurements.when_captured, 'YYYY-MM-DD" "HH24:MI:SSOF') as when_captured,
                to_char(measurements.lnd_7318u / 334.0, '990D999') as lnd_7318u
            FROM devices, measurements
            WHERE devices.id = measurements.device
                AND devices.urn = %(device_urn)s
            ORDER BY measurements.when_captured DESC
            LIMIT 10
        """,
        {"device_urn": urn})
    data = []
    for row in curs.fetchall():
        data.append(row)
    # The timestampTZ format is compatible with expected return value
    # See experiment in Thonny
    return data


connstring = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS}"
conn = psycopg.connect(connstring, row_factory=dict_row)
print(get_device_measurement_history(conn, 'geigiecast:63209', 30))
