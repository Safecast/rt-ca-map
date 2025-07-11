'''fetcher.py - Fetch latest data from Safecast database (TT server).
'''

import asyncio
import httpx
import json

import database
from constants import SAFECAST_API_BASE, INITIAL_DEVICE_URNS

async def fetch_latest_device(urn: str):
    async with httpx.AsyncClient() as client:
        url = f'{SAFECAST_API_BASE}/device/{urn}'
        print(f'Fetching {url}')
        response = await client.get(url)
        response.raise_for_status()
        resp_text = response.text
        if len(resp_text) < 100 or resp_text.startswith == 'no such':
            raise httpx.RequestError(f"Error: Device_urn {urn} not found on database server.")
        try:
            resp_data = response.json()
        except json.JSONDecodeError as exc:
            print(f"Exception decoding response from the database server:\n  {exc.msg}.",)
            raise httpx.RequestError("Improper response from the database server for device_urn {urn}.")
        except UnicodeDecodeError as exc:
            print(f"Improper UTF-8 encoding in response from the database server:\n  {exc}")
            raise httpx.RequestError("Improper response from the database server for device_urn {urn}.")
        await database.db_save_current_values(resp_data)

async def fetch_all_latest():
    '''Get the list of active devices from the database.
    '''
    active_devices = database.get_active_devices()  # Returns a list of device_urn
    for urn in active_devices:
        try:
            await fetch_latest_device(urn)
            print(f"Fetched {urn}")
        except httpx.RequestError as exc:
            # Note: the !r in the format string prints the url using the repr() method 
            print(f"Error while fetching device_urn {urn}:\n  {exc}")

async def periodic(interval_sec, coro_name, *args, **kwargs):
    ''' Helper function for running a target periodically.
    '''
    # loop forever
    while True:
        # wait an interval
        await asyncio.sleep(interval_sec)
        # await the target
        await coro_name(*args, **kwargs)

async def bootstrap_database():
    ''' Helper function to initialize the database with the devices
    in a fixed list constants.INITIAL_DEVICE_URNS.
    TODO: Have the admin page start empty and 
        the site administrator adds the devices.
    '''
    for device_urn in INITIAL_DEVICE_URNS:
        await fetch_latest_device(device_urn)

if __name__ == '__main__':
    print("Testing. Normally, you would simply import this module.")
    asyncio.run(fetch_all_latest())

