import logging
import falcon.asgi
import pathlib
from jinja2 import Environment, PackageLoader, select_autoescape
import json
import asyncio

# Local imports
import devices
import fetcher


# # TODO: Finish this!
# class Devices:
#     def __init__(self) -> None:
#         pass
#     async def get_device(self, devicenumber: str) -> dict:
#         '''Return a dict for a single device, for example
#             device_urn: str ex. geigiecast-zen:65004
#             device_id: int ex. 65004
#             device_class: str e.x. geigiecast
#             last_seen: timestampTZ ex. "2025-06-01T22:02:48Z"
#             latitude: real as a float ex. 44.10849
#             longitude: real as a float ex. 7524
#             last_reading: integer as a float ex. 29 (from "lnd_7318u")
#         '''
#         try:
#             id = int(devicenumber)
#         except ValueError as err:
#             raise falcon.HTTPInvalidParam('Invalid device ID, must be numeric.', device_id)
#         loop = asyncio.get_running_loop()
#         device_data = await loop.run_in_executor(None, database.get_device_measurement, id)
#         #         loop = asyncio.get_running_loop()
#         # image = await loop.run_in_executor(None, self._load_from_bytes, data)
#         if device_data:
#             return device_data
#         else:
#             print("devices:get_device(): empty device data.")
#             return None


# Set up logging
logpath = pathlib.Path.cwd() / pathlib.Path("logs")
logpath.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=logpath/"app.log", level=logging.INFO)
logger = logging.getLogger(__name__)

# Templates
# Set up templates
templates_env = Environment(
    loader=PackageLoader("maps"),
    autoescape=select_autoescape()
)

class Map:
    def __init__(self):
        self._foo = "Foo!"
    async def on_get(self, req, resp):
        logger.info(f"Map.on_get: Entry with req = {req}.")
        # headers = []
        # for h in req.scope["headers"]:
        #     headers.append(h)
        # logger.info(f"  headers = {headers}")
        assert req.scope["type"] == "http"

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML
        template = templates_env.get_template("index.html")
        resptext = template.render({"request": req})
        logger.info(f"Map.on_get: template = {resptext}.")
        resp.text = resptext


class Devices:
    '''Respond to API requests.'''
    def __init__(self) -> None:
        pass
    async def on_get(self, req, resp):
        '''Return the list of devices with their latest readings.'''
        logger.info(f"API.on_get: Entry, req = {req}, uri = {req.uri}")
        logger.info(f"API.on_get: Calling get_devices.")
        text = devices.Devices().get_devices()
        # text = {"message": "Hello API."}
        logger.info(text)
        resp.media = text
        resp.status = falcon.HTTP_200

class Measurements:
    '''Respond to request for measurements.'''
    def __init__(self) -> None:
        pass
    async def on_get(self, req, resp, device_urn):
        '''Return the list of measurements with their latest readings.'''
        logger.info(f"Measurements.on_get: Entry, req = {req}, uri = {req.uri}, device_urn {device_urn}")
        headers = []
        for h in req.scope["headers"]:
            headers.append(h)
        logger.info(f"  headers = {headers}")
        # scope_list = []
        # for k,v in req.scope:
        #     scope_list.append(f"{k}:{v}")
        logger.info(f"  scope = {req.scope}")
        logger.info(f"  params = {req.params}")
        assert req.scope["type"] == "http"
        # logger.info(f"Measurements.on_get: Calling get_devices.")
        # text = devices.Devices().get_devices()
        days = req.params["days"]
        # days = querystring.split("=")[1]
        # text = {"message": f"Hello measurements, devicenumber={device_urn} days={days}."}
        text = devices.Devices().get_device_history(device_urn, days)
        logger.info(text)
        resp.media = text
        resp.status = falcon.HTTP_200


    # async def on_get(self, req, resp, devicenumber):
    #     '''Return the dict for a single device's latest reading.'''
    #     logger.info(f"API.on_get: Entry with req = {req} and devicenumber {devicenumber}.")
    #     # resp.content_type = falcon.MEDIA_HTML
    #     # data = devices.Devices.get_device(devicenumber)
    #     text = devices.Devices().get_device(devicenumber)
    #     # text = {"message": "Hello API."}
    #     logger.info(text)
    #     resp.media = text
    #     resp.status = falcon.HTTP_200

def create_app(config=None):
    # config = config or Config()
    logger.info(f"create_app: Creating new falcon.asgi.App.")

    measurements = Measurements()
    devices = Devices()
    maps = Map()
    app = falcon.asgi.App()
    # Map
    logger.info("create_app: Creating new route /map.")
    app.add_route('/map', maps)
    # List of devices
    logger.info("create_app: Creating new route /devices.")
    app.add_route('/devices', devices)
    # List of measurements
    logger.info(r"create_app: Creating new route /measurements/{devicenumber}.")
    app.add_route('/measurements/{device_urn}', measurements)

    # Starting background fetcher task
    coroutine = fetcher.fetch_all_latest
    # create and schedule the periodic task
    task = asyncio.create_task(fetcher.periodic(180.0, coroutine))

    # while True:
    #     await fetcher.fetch_all_latest())
    #     asyncio.sleep(60)
    return app

