'''pgsql_testing.py - Various tests with psycopg and PostgreSQL
'''
import psycopg
from psycopg.rows import dict_row
import json
from datetime import datetime, timedelta, timezone


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

def get_device_measurement_history(urn: str, hours: int = 24) -> list:
    '''Return a list of dict of historical readings for a single device,
    with each entry in the list as a dict, for example
            when_captured: timestamp with time zone
            lnd_7318u: integer as a float
    '''
    # Determine the appropriate time scale, depending on the number of data points
    nowtime = datetime.now(timezone.utc)
    # starttime = nowtime - timedelta(hours=int(hours))
    # backtrack = f"'{starttime.isoformat(sep=' ', timespec='minutes')}'"
    backtrack = '2025-07-16 17:07+00:00'
    print(backtrack)
    curs = conn.cursor()
    curs.execute("""
        SELECT devices.urn as device_urn, 
                to_char(measurements.when_captured, 'YYYY-MM-DD" "HH24:MIOF') as when_captured,
                to_char(measurements.lnd_7318u / 334.0, '990D999') as lnd_7318u
            FROM devices, measurements
            WHERE devices.id = measurements.device
                AND devices.urn = %(device_urn)s
                AND when_captured >= %(backtrack)s
            ORDER BY measurements.when_captured DESC
            -- LIMIT 10
        """,
        {"device_urn": urn, "backtrack": backtrack})
    data = []
    for row in curs.fetchall():
        data.append(row)
    # assert len(data) > 30, f'Number of data points = {len(data)}, PG result = {curs.statusmessage}\n'

    # The timestampTZ format is compatible with expected return value
    # See experiment in Thonny

    samples = []  # Output list

    # If there are no samples returned from the query,
    # make up the amount of zero samples to satisfy the hours parameter.
    if len(data) == 0:
        timenow = datetime.now(timezone.utc)
        missing = 1
        for i in range(hours * (60//5)):
                inserttime = timenow - timedelta(seconds=missing*5*60)
                newitem = {'device_urn': urn,
                        'when_captured': inserttime.isoformat(sep=' ', timespec='minutes'),
                        'lnd_7318u': '   0.000'}
                samples.append(newitem)
                missing += 1
        return samples
    # Insert zero value samples for gaps in the record. Assume 5 minute intervals for now.
    newtime = datetime.fromisoformat(data[0]["when_captured"]) - timedelta(minutes=5)
    # print(f"new time = {newtime}")
    idx = 0
    while idx < len(data) - 1:
        item = data[idx]
        when_captured = datetime.fromisoformat(item["when_captured"])
        nexttime = datetime.fromisoformat(data[idx+1]["when_captured"])
        interval = (when_captured - nexttime).seconds
        if interval <= 5.5 * 60:  # 5 minutes+0.5 minute
            samples.append(item)
        else:
            print(when_captured, interval)
            samples.append(item)
            missing = 1
            while interval > 5.5 * 60:
                inserttime = when_captured - timedelta(seconds=missing*5*60)
                newitem = {'device_urn': urn,
                        'when_captured': inserttime.isoformat(sep=' ', timespec='minutes'),
                        'lnd_7318u': '   0.000'}
                samples.append(newitem)
                interval -= 5*60
                missing += 1
        idx += 1
    return samples


connstring = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS}"
conn = psycopg.connect(connstring, row_factory=dict_row)
print(get_device_measurement_history('geigiecast-zen:65004', 2))
