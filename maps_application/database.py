'''database.py - Application database operations.
Import this as a module to keep the main file lightweight.

'''
import psycopg
import json
import asyncio

# Local
from constants import DB_CONNECT

# Prepared SQL statements
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
SQL_SELECT_DEVICES = """
    SELECT COUNT(*) FROM devices
        WHERE device = %(device)s;
    """
SQL_INSERT_DEVICES = """
    INSERT INTO devices (device, urn, device_class)
        VALUES (%(device)s, %(urn)s, (SELECT id FROM device_classes WHERE class = %(device_class)s));
    """
SQL_INSERT_MEASUREMENT = """
    INSERT INTO measurements (device, when_captured, loc_lat, loc_lon, lnd_7318u, transport)
        VALUES (%(device)s, %(when_captured)s, %(loc_lat)s, %(loc_lon)s, %(lnd_7318u)s, 
            (SELECT id FROM transports WHERE service_transport = %(service_transport)s));
    """


async def db_save_current_values(safecast_data: dict) -> None:
    '''Take the entire dict returned from a device query to the TT database server
    and update the database classes, transports, devices and measurements.'''
    # Connect to an existing database
    current_values = safecast_data["current_values"]
    transport_ip_info = safecast_data["transport_ip_info"]
    with psycopg.connect(**DB_CONNECT) as conn:
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
        curs.execute(SQL_SELECT_DEVICES, {"device": current_values["device"]})
        if curs.fetchone()[0] == 0:
            # Not already there, insert new
            curs.execute(SQL_INSERT_DEVICES, 
                         {"device": current_values["device"],
                          "urn": current_values["device_urn"],
                          "device_class": current_values["device_class"]})

        # Finally (oof) insert the new measurement
        try:
            curs.execute(SQL_INSERT_MEASUREMENT,
                     {
                         "device": current_values["device"],
                         "when_captured": current_values["when_captured"],
                         "loc_lat": current_values["loc_lat"],
                         "loc_lon": current_values["loc_lon"],
                         "lnd_7318u": current_values["lnd_7318u"],
                         "service_transport": current_values["service_transport"]
                     })
            conn.commit()  # Finally, down here, we can commit the entire transaction
        except psycopg.IntegrityError as err:
            print(f"Error saving new measuremen:\n  {err}")
            conn.rollback()
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

