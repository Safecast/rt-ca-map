import logging
import falcon.asgi
import pathlib
from jinja2 import Environment, PackageLoader, select_autoescape
import json
import asyncio

# Local imports
import devices
import fetcher
import admin

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
        pass

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
        logger.info(f"Map.on_get: returning template index.html.")
        resp.text = resptext


class Measurements:
    '''Respond to request for measurements.'''
    def __init__(self, devices) -> None:
        self._devices = devices  # Keep working with same instance of the class

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
        try:
            hours = req.params["hours"]
        except KeyError:
            hours = 24  # Default for the last 24 hours.
        text = self._devices.get_device_history(device_urn, hours)
        # logger.info(json.dumps(text, indent=2))
        resp.media = text
        resp.status = falcon.HTTP_200


def create_app(config=None):
    # config = config or Config()
    logger.info(f"create_app: Creating new falcon.asgi.App.")

    devs = devices.Devices()
    maps = Map()
    measurements = Measurements(devs)
    administration = admin.Admin(devs)
    app = falcon.asgi.App()
    # Map
    logger.info("create_app: Creating new route /map.")
    app.add_route('/map', maps)
    # List of devices
    logger.info("create_app: Creating new route /devices.")
    app.add_route('/devices', devs)
    # List of measurements
    logger.info("create_app: Creating new route /measurements/{device_urn}.")
    app.add_route('/measurements/{device_urn}', measurements)
    # Administration page
    logger.info("create_app: Creating new route /admin.")
    app.add_route('/admin', administration)

    # Starting background fetcher task
    coroutine = fetcher.fetch_all_latest
    # create and schedule the periodic task (1 minute)
    task = asyncio.create_task(fetcher.periodic(60.0, coroutine))

    return app

