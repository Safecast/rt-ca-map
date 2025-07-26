'''database.py - Application database operations.
Import this as a module to keep the main file lightweight.

TODO: Check that the when_captured is not in the future by more than a few seconds.
TODO: Check the geiger_history list in the response JSON from the server to
      make sure that we didn't miss any. If so, back fill. The history doesn't
      have the location therefore simply copy the previous loc_lat and loc_lon.
'''

import psycopg
from psycopg.rows import dict_row
import json
import asyncio
from datetime import datetime, timedelta, timezone

# Local
from constants import DB_HOST, DB_NAME, DB_USER, DB_PASS

class Database:
    def __init__(self) -> None:
        connstring = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS}"
        self._conn = psycopg.connect(connstring, row_factory=dict_row)

    def get_managed_devices(self):
        '''Return list of device dicts, each dict:
            'device_urn',
            'device_class',
            'last_seen',
            'active',
            'display'
        '''
        curs = self._conn.cursor()
        curs.execute("""
            SELECT devices.urn as device_urn, devices.id as "device_id",
                device_classes.class as device_class, devices.last_seen as last_seen,
                devices.active, devices.display
            FROM devices, device_classes
            WHERE
                devices.device_class = device_classes.id
            ORDER BY devices.urn ASC;
            """)
        return curs.fetchall()

    def get_device_measurement_history(self, urn: str, hours: int = 24) -> list:
        '''Return a list of dict of historical readings for a single device,
        with each entry in the list as a dict, for example
                when_captured: timestamp with time zone
                lnd_7318u: integer as a float
        Insert zero value samples for gaps in the record. Assume 5 minute intervals for now.
        If there are no samples returned from the database query, the function
        makes up the amount of zero samples to satisfy the hours parameter.

        '''
        SAMPLING_INTERVAL = 5  # minutes
        nowtime = datetime.now(timezone.utc)
        starttime = nowtime - timedelta(hours=hours)
        backtrack = f"'{starttime.isoformat(sep=' ', timespec='minutes')}'"
        curs = self._conn.cursor()
        curs.execute("""
            SELECT devices.urn as device_urn, 
                    to_char(measurements.when_captured, 'YYYY-MM-DD" "HH24:MIOF') as when_captured,
                    to_char(measurements.lnd_7318u / 334.0, '0D999') as lnd_7318u
                FROM devices, measurements
                WHERE devices.id = measurements.device
                    AND devices.urn = %(device_urn)s
                    AND when_captured >= %(backtrack)s
                ORDER BY measurements.when_captured DESC
            """,
            {"device_urn": urn, "backtrack": backtrack})
        data = []
        for row in curs.fetchall():
            data.append(row)
        # DEBUG assert len(data) > 30, f'Number of data points = {len(data)}, PG result = {curs.statusmessage}\n'

        # The timestampTZ format is compatible with expected return value
        # See experiment in Thonny

        samples = []  # Output list

        # If there are no samples returned from the query,
        # make up the amount of zero samples to satisfy the hours parameter.
        if len(data) == 0:
            timenow = datetime.now(timezone.utc)
            missing = 1
            for i in range(hours * (60//SAMPLING_INTERVAL)):
                    inserttime = timenow - timedelta(seconds=missing*5*60)
                    newitem = {'device_urn': urn,
                            'when_captured': inserttime.isoformat(sep=' ', timespec='minutes'),
                            'lnd_7318u': '0.000'}
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
            if interval <= (SAMPLING_INTERVAL +0.5) * 60:  # Typically 5 minutes+0.5 minute
                samples.append(item)
            else:
                # DEBUG print(when_captured, interval)
                samples.append(item)
                missing = 1
                while interval > (SAMPLING_INTERVAL + 0.5) * 60:
                    inserttime = when_captured - timedelta(seconds=missing*SAMPLING_INTERVAL*60)
                    newitem = {'device_urn': urn,
                            'when_captured': inserttime.isoformat(sep=' ', timespec='minutes'),
                            'lnd_7318u': '0.000'}
                    samples.append(newitem)
                    interval -= SAMPLING_INTERVAL*60
                    missing += 1
            idx += 1
        return samples


    def get_device_measurement(self, urn: str):
        '''Return a dict for a single device, for example
            device_urn: str ex. geigiecast-zen:65004
            device_class: str e.x. geigiecast
            last_seen: timestampTZ formatted as "2025-06-01 22:02:48+00"
            latitude: real as a float ex. 44.10849
            longitude: real as a float ex. -78.75195
            last_reading: integer as a float ex. 29 (from "lnd_7318u")
        '''
        curs = self._conn.cursor()
        curs.execute("""
            SELECT devices.urn as device_urn, device_classes.class as device_class,
                    to_char(measurements.when_captured, 'YYYY-MM-DD" "HH24:MI:SSOF') as last_seen,
                    measurements.loc_lat as latitude, measurements.loc_lon as longitude,
                    measurements.lnd_7318u as last_reading
                FROM devices, measurements, device_classes
                WHERE devices.id = measurements.device
                    AND device_classes.id = devices.device_class
                    AND devices.urn = %(urn)s
                ORDER BY measurements.when_captured DESC
                LIMIT 1;
            """,
            {"urn": urn})
        data = curs.fetchone()
        # TODO: check the timestampTZ format to be compatible with expected return value
        # See experiment in Thonny
        return data

    def get_device_list(self):
        curs = self._conn.cursor()
        curs.execute("""
            SELECT id FROM devices
                WHERE display = TRUE AND active = TRUE;
            """)
        dev_list = []
        for dev in curs.fetchall():
            dev_list.append(int(dev["device"]))
        return dev_list

    def activate_device(self, device_urn: str, activate: bool = True) -> int:
        curs = self._conn.cursor()
        curs.execute("""
            UPDATE devices
                SET active = %(status)s
                WHERE devices.urn = %(device_urn)s 
            """,
            {"status": str(activate).upper(), "device_urn": device_urn})
        return curs.rowcount

# Note: this is a static function because it is called from fetcher, not the app.
def get_active_devices():
    '''Return a list of device URN e.g. "geigiecast:62106".
    This is a static function, not part of class Database because it is called
    by the fetcher.
    '''
    connstring = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS}"
    with psycopg.connect(connstring, row_factory=dict_row) as conn:
        curs = conn.cursor()
        curs.execute("""
            SELECT urn FROM devices
                WHERE active = TRUE
                ORDER BY urn ASC;
            """)
        data = []
        for row in curs.fetchall():
            data.append(row["urn"])
        return data


# Prepared SQL statements for function db_save_current_values()
SQL_SELECT_DEVICE_CLASS = """
    SELECT COUNT(*) FROM device_classes
        WHERE class = %(class)s;
    """
SQL_INSERT_DEVICE_CLASS = """
    INSERT INTO device_classes (class)
        VALUES (%(class)s);
    """
SQL_SELECT_TRANSPORTS = """
    SELECT COUNT(*) FROM transports
        WHERE service_transport = %(service_transport)s;
    """
SQL_INSERT_TRANSPORTS = """
    INSERT INTO transports (service_transport, service_uploaded)
        VALUES (%(service_transport)s, %(service_uploaded)s);
    """
SQL_UPDATE_TRANSPORTS = """
    UPDATE transports
        SET service_uploaded = %(service_uploaded)s,
            transport_ip_info = %(transport_ip_info)s
        WHERE service_transport = %(service_transport)s;
    """
SQL_SELECT_DEVICE_COUNT = """
    SELECT COUNT(urn) FROM devices
        WHERE urn = %(urn)s;
    """
SQL_INSERT_DEVICES = """
    INSERT INTO devices (urn, device_class, service_transport, last_seen)
        VALUES (%(urn)s,
            (SELECT id FROM device_classes WHERE class = %(device_class)s),
            (SELECT id FROM transports WHERE service_transport = %(service_transport)s),
            %(last_seen)s
        );
    """
SQL_UPDATE_DEVICES = """
    UPDATE devices
    SET
        device_class = (SELECT id FROM device_classes WHERE class = %(device_class)s),
        service_transport = (SELECT id FROM transports WHERE service_transport = %(service_transport)s),
        last_seen = %(last_seen)s
    WHERE urn = %(urn)s;
    """
SQL_INSERT_MEASUREMENT = """
    INSERT INTO measurements (device, when_captured, loc_lat, loc_lon, lnd_7318u)
        VALUES (
            (select id from devices where devices.urn=%(urn)s), 
            %(when_captured)s, %(loc_lat)s, %(loc_lon)s, %(lnd_7318u)s);
    """

# Note: this is a static function because it is called from fetcher, not the app.
async def db_save_current_values(safecast_data: dict) -> None:
    '''Take the entire dict returned from a device query to the TT database server
    and update the database classes, transports, devices and measurements.
    This is a static function, not part of class Database because it is called
    by the fetcher.
    '''
    # Shorthand variables, each one is a dict from the JSON response.
    current_values:dict = safecast_data["current_values"]
    transport_ip_info:dict = safecast_data["transport_ip_info"]

    # Connect to an existing database
    connstring = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS}"
    with psycopg.connect(connstring) as conn:
        curs = conn.cursor()

        # Check if device_class is known
        curs.execute(SQL_SELECT_DEVICE_CLASS, {"class": current_values["device_class"]})
        if curs.fetchone()[0] == 0:
            # Not already there, insert new
            curs.execute(SQL_INSERT_DEVICE_CLASS, {"class": current_values["device_class"]})

        # Check if service_transport is known
        curs.execute(SQL_SELECT_TRANSPORTS, {"service_transport": current_values["service_transport"]})
        if curs.fetchone()[0] == 0:
            # Not already there, insert new
            curs.execute(SQL_INSERT_TRANSPORTS, 
                         {"service_transport": current_values["service_transport"],
                          "service_uploaded":current_values["service_uploaded"],
                          "transport_ip_info":json.dumps(transport_ip_info)})
        else:
            curs.execute(SQL_UPDATE_TRANSPORTS, 
                         {"service_transport": current_values["service_transport"],
                          "service_uploaded":current_values["service_uploaded"],
                          "transport_ip_info":json.dumps(transport_ip_info)})

        # Check if the device is known
        curs.execute(SQL_SELECT_DEVICE_COUNT, {"urn": current_values["device_urn"]})
        if curs.fetchone()[0] == 0:
            # Not already there, insert new
            curs.execute(SQL_INSERT_DEVICES, 
                         {  # no longer used "device": current_values["device"],
                          "urn": current_values["device_urn"],
                          "device_class": current_values["device_class"],
                          "service_transport": current_values["service_transport"],
                          "last_seen":current_values["when_captured"],
                        })
        else:
            # Update the information
            curs.execute(SQL_UPDATE_DEVICES, 
                         {
                          "urn": current_values["device_urn"],
                          "device_class": current_values["device_class"],
                          "service_transport": current_values["service_transport"],
                          "last_seen":current_values["when_captured"],
                        })

        # Finally (oof) insert the new measurement
        try:
            curs.execute(SQL_INSERT_MEASUREMENT,
                     {
                         "urn": current_values["device_urn"],
                         "when_captured": current_values["when_captured"],
                         "loc_lat": current_values["loc_lat"],
                         "loc_lon": current_values["loc_lon"],
                         "lnd_7318u": current_values["lnd_7318u"],
                     })
            conn.commit()  # Finally, down here, we can commit the entire transaction
        except psycopg.IntegrityError as err:
            print(f"Error saving new measurement:\n  {err}")
            conn.rollback()  # Roll back the entire transaction
            return
    return

if __name__ == '__main__':
    print('Please import this as a module.')

    # Testing
    ttdata = {
        "current_values": {
            "device_urn": "geigiecast:62106",
            "device_class": "geigiecast",
            "device": 62106,
            "when_captured": "2025-06-01T22:02:48Z",
            "loc_lat": 44.10849,
            "loc_lon": -78.7524,
            "lnd_7318u": 29,
            "service_uploaded": "2025-06-01T22:03:53Z",
            "service_transport": "geigiecast:216.59.235.178"
        },
        "transport_ip_info": {
            "query": "216.59.235.178",
            "status": "success",
            "as": "AS7794 Execulink Telecom Inc.",
            "city": "Tillsonburg",
            "country": "Canada",
            "countryCode": "CA",
            "isp": "Execulink Telecom Inc.",
            "lat": 42.8568,
            "lon": -80.7294,
            "org": "Execulink Telecom Inc.",
            "region": "ON",
            "regionName": "Ontario",
            "timezone": "America/Toronto",
            "zip": "N4G"
        }

    }

    ttdata2 = {
    "current_values": {
        "device_urn": "geigiecast-zen:65049",
        "device_class": "geigiecast-zen",
        "device": 65049,
        "when_captured": "2025-06-01T22:00:37Z",
        "loc_lat": 43.88204,
        "loc_lon": -78.94496,
        "lnd_7318u": 22,
        "service_uploaded": "2025-06-01T22:00:37Z",
        "service_transport": "geigiecast-zen:142.112.172.27"
    },
    "location_history": [
        {},
        {},
        {},
        {},
        {}
    ],
    "geiger_history": [
        {
            "device_urn": "geigiecast-zen:65049",
            "device": 65049,
            "when_captured": "2025-06-01T21:55:37Z",
            "lnd_7318u": 22
        },
        {
            "device_urn": "geigiecast-zen:65049",
            "device": 65049,
            "when_captured": "2025-06-01T21:50:36Z",
            "lnd_7318u": 21
        },
        {
            "device_urn": "geigiecast-zen:65049",
            "device": 65049,
            "when_captured": "2025-06-01T21:45:33Z",
            "lnd_7318u": 23
        },
        {
            "device_urn": "geigiecast-zen:65049",
            "device": 65049,
            "when_captured": "2025-06-01T21:40:29Z",
            "lnd_7318u": 22
        },
        {
            "device_urn": "geigiecast-zen:65049",
            "device": 65049,
            "when_captured": "2025-06-01T21:35:29Z",
            "lnd_7318u": 26
        }
    ],
    "opc_history": [
        {},
        {},
        {},
        {},
        {}
    ],
    "pms_history": [
        {},
        {},
        {},
        {},
        {}
    ],
    "pms2_history": [
        {},
        {},
        {},
        {},
        {}
    ],
    "transport_ip_info": {
        "query": "142.112.172.27",
        "status": "success",
        "as": "AS577 Bell Canada",
        "city": "Whitby",
        "country": "Canada",
        "countryCode": "CA",
        "isp": "Bell Canada",
        "lat": 43.9228,
        "lon": -78.9412,
        "org": "Sympatico HSE",
        "region": "ON",
        "regionName": "Ontario",
        "timezone": "America/Toronto",
        "zip": "L1R"
    }
}
    
    asyncio.run(db_save_current_values(ttdata2))

