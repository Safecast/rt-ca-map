'''devices.py - Class Devices to represent devices in the database.
'''

import falcon
import asyncio

# Local
import database

# TODO: Finish this!
class Devices:
    def __init__(self) -> None:
        pass
    async def get_device(device_id: str) -> dict:
        '''Return a dict for a single device, for example
            device_urn: str ex. geigiecast-zen:65004
            device_id: int ex. 65004
            device_class: str e.x. geigiecast
            last_seen: timestampTZ ex. "2025-06-01T22:02:48Z"
            latitude: real as a float ex. 44.10849
            longitude: real as a float ex. 7524
            last_reading: integer as a float ex. 29 (from "lnd_7318u")
        '''
        try:
            id = int(device_id)
        except ValueError as err:
            raise falcon.HTTPInvalidParam('Invalid device ID, must be numeric.', device_id)
        loop = asyncio.get_running_loop()
        device_data = await loop.run_in_executor(None, database.get_device_measurement, id)
        #         loop = asyncio.get_running_loop()
        # image = await loop.run_in_executor(None, self._load_from_bytes, data)
        if device_data:
            return device_data
        else:
            print("devices:get_device(): empty device data.")
            return None

# async def get_devices():
#     try:
#         with get_db() as conn:
#             try:
#                 # First, check if transport_info table exists
#                 table_exists = False
#                 try:
#                     check_table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transport_info'").fetchone()
#                     table_exists = check_table is not None
#                 except Exception as table_error:
#                     logger.warning(f"Error checking if transport_info table exists: {table_error}")
#                     table_exists = False
                
#                 # First, get all devices
#                 devices_query = """
#                     SELECT device_urn, device_id, device_class, last_seen, latitude, longitude, last_reading
#                     FROM devices
#                 """
                
#                 devices_result = conn.execute(devices_query).fetchall()
                
#                 if not devices_result:
#                     return {"devices": []}
                
#                 devices = []
#                 for device_row in devices_result:
#                     try:
#                         device_urn = device_row[0]
#                         device_id = device_row[1]
#                         device_class = device_row[2]
#                         last_seen = device_row[3]
#                         latitude = device_row[4]
#                         longitude = device_row[5]
#                         last_reading = device_row[6]
                        
#                         # Get transport info if the table exists
#                         transport_result = None
#                         if table_exists:
#                             try:
#                                 transport_query = """
#                                     SELECT city, country 
#                                     FROM transport_info 
#                                     WHERE device_urn = ?
#                                     LIMIT 1
#                                 """
#                                 transport_result = conn.execute(transport_query, (device_urn,)).fetchone()
#                             except Exception as transport_error:
#                                 logger.warning(f"Error fetching transport info for device {device_urn}: {transport_error}")
                        
#                         # Build device data
#                         device_data = {
#                             "device_urn": device_urn,
#                             "device_id": device_id,
#                             "device_class": device_class,
#                             "latitude": float(latitude) if latitude is not None else None,
#                             "longitude": float(longitude) if longitude is not None else None,
#                             "last_seen": last_seen.isoformat() if hasattr(last_seen, 'isoformat') else str(last_seen) if last_seen else None,
#                             "last_reading": float(last_reading) if last_reading is not None else None,
#                             "location": None
#                         }
                        
#                         # Add location string if transport info is available
#                         if transport_result and transport_result[0] and transport_result[1]:
#                             device_data["location"] = f"{transport_result[0]}, {transport_result[1]}"
                        
#                         devices.append(device_data)
#                     except Exception as device_error:
#                         logger.error(f"Error processing device row {device_row}: {device_error}")
#                         continue
                
#                 return {"devices": devices}
                
#             except Exception as query_error:
#                 logger.error(f"Database query error in get_devices: {query_error}")
#                 logger.error(traceback.format_exc())
#                 raise HTTPException(status_code=500, detail=f"Database query error: {str(query_error)}")
                
#     except HTTPException:
#         raise  # Re-raise HTTP exceptions
#     # except Exception as e:
#     #     error_msg = f"Unexpected error in get_devices: {str(e)}"
#     #     logger.error(error_msg)
#     #     logger.error(traceback.format_exc())
#     #     raise HTTPException(status_code=500, detail=error_msg)
