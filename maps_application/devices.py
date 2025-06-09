'''devices.py - Class Devices to represent devices in the database.
'''

import falcon
import asyncio
import json
import pathlib
import logging
import httpx

# Local
import database
import fetcher


class Devices:
    '''Manage devices and respond to API requests.'''
    def __init__(self) -> None:
        # Set up logging
        self.logpath = pathlib.Path.cwd() / pathlib.Path("logs")
        self.logpath.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=self.logpath/"devices_app.log", level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        # Managed devices
        self._devices_managed = database.get_managed_devices()

    async def on_get(self, req, resp):
        '''Return the list of devices with their latest readings.'''
        self.logger.info(f"API.on_get: Entry, req = {req}, uri = {req.uri}")
        self. logger.info(f"API.on_get: Calling get_devices_list.")
        text = self.get_devices_list()
        # text = {"message": "Hello API."}
        self.logger.info(text)
        resp.media = text
        resp.status = falcon.HTTP_200

    async def add_device(self, device_urn: str) -> bool:
        '''If device not already known in the database, wait for fetcher to do its job.'''
        devices = database.get_managed_devices()
        for dev in devices:
            # If already there, return True
            if dev["device_urn"] == device_urn:
                raise Exception("Add device already there.")
                # return True
        await fetcher.fetch_latest_device(device_urn)
        return True

    def activate_device(self, device_urn: str, active: bool = True) -> int:
        '''Set the device.active flag to False.
        Normally return True.
        Return False if the device URN is not known locally.'''
        return database.activate_device(device_urn, active)


    def get_device(self, devicenumber: str) -> dict:
        '''Return a dict for a single device, for example
            device_urn: str ex. geigiecast-zen:65004
            device_id: int ex. 65004
            device_class: str e.x. geigiecast
            last_seen: timestampTZ ex. "2025-06-01T22:02:48Z"
            latitude: real as a float ex. 44.10849
            longitude: real as a float ex. 7524
            last_reading: integer as a float ex. 29 (from "lnd_7318u")
            location: None  (temporarily)
        '''
        try:
            id = int(devicenumber)
            # logger.info(f"get_device: {device_data}")
        except ValueError as err:
            raise falcon.HTTPInvalidParam('Invalid device ID, must be numeric.', device_id)
        # loop = asyncio.get_running_loop()
        # device_data = {"message": f"The device number is {id}."} 
        device_data = database.get_device_measurement(id)
        # loop.run_in_executor(None, database.get_device_measurement, id)
        #         loop = asyncio.get_running_loop()
        # image = await loop.run_in_executor(None, self._load_from_bytes, data)
        # logger.info(f"get_device: {device_data}")
        if device_data:
            # data_json = json.dumps(device_data, indent=2)
            # yield data_json
            device_data["location"] = None
            return device_data
        else:
            print("devices:get_device(): empty device data.")
            return {"message": "No device data."}

    def get_devices_list(self):
        devices = database.get_device_list()
        device_data = []
        for dev in devices:
            device_data.append(self.get_device(dev))
        return {"devices": device_data}

    def get_device_history(self, urn, days):
        device_data = database.get_device_measurement_history(urn, days)
        # device_data = []
        # for dev in devices:
        #     device_data.append(self.get_device(dev))
        return {"measurements": device_data}

    def get_devices_managed(self):
        device_data = database.get_managed_devices()
        active_devs = []
        inactive_devs = []
        for dev in device_data:
            if dev["active"]:
                active_devs.append(dev)
            else:
                inactive_devs.append(dev)
        return active_devs, inactive_devs

