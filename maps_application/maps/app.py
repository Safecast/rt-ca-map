import logging
import falcon.asgi
import pathlib
from jinja2 import Environment, PackageLoader, select_autoescape
import json
import asyncio

# Local imports
import devices
import fetcher


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

# # Moved to module devices
# class Devices:
    # '''Respond to API requests.'''
    # def __init__(self) -> None:
    #     pass
    # async def on_get(self, req, resp):
    #     '''Return the list of devices with their latest readings.'''
    #     logger.info(f"API.on_get: Entry, req = {req}, uri = {req.uri}")
    #     logger.info(f"API.on_get: Calling get_devices_list.")
    #     text = devices.Devices().get_devices_list()
    #     # text = {"message": "Hello API."}
    #     logger.info(text)
    #     resp.media = text
    #     resp.status = falcon.HTTP_200

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
        days = req.params["days"]
        text = devices.Devices().get_device_history(device_urn, days)
        logger.info(text)
        resp.media = text
        resp.status = falcon.HTTP_200


class Admin:
    '''Respond to administrative requests.'''
    def __init__(self, devices) -> None:
        self._devices = devices  # Keep working with same instance of the class
        pass

    async def on_get(self, req, resp):
        '''Display the admin page with existing settings.'''
        logger.info(f"Admin.on_get: Entry, req = {req}, uri = {req.uri}.")
        device_data, deleted_devices = self._devices.get_devices_managed()
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML
        template = templates_env.get_template("admin.html")
        resptext = template.render({
                    "request": req, 
                    "devices": device_data,
                    "deleted_devices": deleted_devices
                }
            )
        logger.info(f"Map.on_get: returning template admin.html.")
        resp.text = resptext

    async def on_post(self, req, resp):
        logger.info(f"Admin.on_post: Entry, req = {req}, uri = {req.uri}.")
        data = await req.stream.read()
        params = data.decode('utf-8')
        # logger.info(f"  req.stream decoded = {params}")
        posted = json.loads(params)
        logstring = f"posted = {type(posted)}\n"
        for k in posted:
            logstring += "  " + k + ": " + str(posted[k]) + "\n"
        # logger.info(f"  posted dict = {posted}")
        logger.info(f"  posted dict contents = {logstring}")
        # resp.status = falcon.HTTP_200
        # resp.text = {"message": f"Scope printed."}

        if posted["command"] == "add_device":
            device_urn = posted['device_urn']
            succcess = await self._devices.add_device(device_urn)
            if succcess:
                resp.status = falcon.HTTP_200
                resp.text = {"message": f"Device {posted['device_urn']} added (Debug, not really)."}
            else:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.text = {"message": f"Device {posted['device_urn']} not in database (Debug, not really)."}

        elif posted["command"] == "delete_device":
            succcess = self._devices.activate_device(posted['device_urn'], active=False)
            if succcess:
                resp.status = falcon.HTTP_200
                resp.text = {"message": f"Device {posted['device_urn']} deactivated."}
            else:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.text = {"message": f"Device {posted['device_urn']} not in database."}

        else:
            resp.status = falcon.HTTP_200
            resp.text = {"message": f"Command {posted['command']} not recognized."}


def create_app(config=None):
    # config = config or Config()
    logger.info(f"create_app: Creating new falcon.asgi.App.")

    measurements = Measurements()
    maps = Map()
    devs = devices.Devices()
    admin = Admin(devs)
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
    app.add_route('/admin', admin)

    # Starting background fetcher task
    coroutine = fetcher.fetch_all_latest
    # create and schedule the periodic task (4 minutes)
    task = asyncio.create_task(fetcher.periodic(240.0, coroutine))

    return app

