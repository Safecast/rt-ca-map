'''devices.py - Class Devices to represent devices in the database.
'''

import falcon
import asyncio
import json
from pathlib import Path
import logging
import httpx
from datetime import datetime, timedelta

# Local
import database
# import fetcher


class Devices:
    '''Manage devices and respond to API requests.
    '''
    def __init__(self) -> None:
        # Set up logging
        self.logpath = Path.cwd() / Path("logs")
        self.logpath.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=self.logpath/"devices_app.log", level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        # Connection to the database
        self._mapsdb = database.Database()

    async def on_get(self, req, resp):
        '''Return the list of devices with their latest readings.'''
        self.logger.info(f"Devices.on_get: Entry, req = {req}, uri = {req.uri}")
        self. logger.info(f"Devices.on_get: Calling get_devices_list.")
        text = self.get_devices_list()
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


    def get_device(self, device_urn: str) -> dict:
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
        self.logger.info(f"Devices.get_device: getting info on {device_urn}.")
        device_data = self._mapsdb.get_device_measurement(device_urn)
        if device_data:
            device_data["location"] = None
            return device_data
        else:
            self.logger.info(f"devices:get_device(): empty device data for {devicenumber}.")
            return {"message": "No device data."}

    def get_devices_list(self):
        '''Return {"devices": devlist}, 
        where devlist is list of device URNs of 
        active and displayable devices.'''
        self.logger.info(f"Devices.get_devices_list: getting info.")
        devlist = []
        for dev in self._mapsdb.get_managed_devices():
            self.logger.info(f"Devices.get_devices_list: getting device_urn: {dev['device_urn']}")
            if dev["active"] and dev["display"]:
                devlist.append(self._mapsdb.get_device_measurement(dev['device_urn']))
        self.logger.info(f"Devices.get_devices_list: {devlist}")
        return {"devices": devlist}

    def get_device_history(self, urn, days):
        device_data = self._mapsdb.get_device_measurement_history(urn, days)
        return {"measurements": device_data}

    def get_devices_managed(self):
        device_data = self._mapsdb.get_managed_devices()
        active_devs = []
        inactive_devs = []
        for dev in device_data:
            if dev["active"]:
                active_devs.append(dev)
            else:
                inactive_devs.append(dev)
        return active_devs, inactive_devs
