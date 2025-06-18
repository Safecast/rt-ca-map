'''admin.py - Administrative page.

'''
import falcon
from jinja2 import Environment, PackageLoader, select_autoescape
import logging
import asyncio
import pathlib
import json

# Local imports
import devices
import fetcher


# Set up logging
logpath = pathlib.Path.cwd() / pathlib.Path("logs")
logpath.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=logpath/"app-admin.log", level=logging.INFO)
logger = logging.getLogger(__name__)

# Templates
# Set up templates
templates_env = Environment(
    loader=PackageLoader("maps"),
    autoescape=select_autoescape()
)


class Admin:
    '''Respond to administrative requests.'''
    def __init__(self, devices) -> None:
        self._devices = devices  # Keep working with same instance of the class

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
            logger.info(f"Map.on_post: command=add_device: adding {device_urn}.")
            succcess = await self._devices.add_device(device_urn)
            if succcess:
                resp.status = falcon.HTTP_200
                device_data, deleted_devices = self._devices.get_devices_managed()
                resp.content_type = falcon.MEDIA_HTML
                template = templates_env.get_template("admin.html")
                resptext = template.render({
                            "request": req, 
                            "devices": device_data,
                            "deleted_devices": deleted_devices
                        }
                    )
                logger.info(f"Map.on_post: command=add_device: successfully added {device_urn}.")
                resp.text = resptext
            else:
                logger.info(f"Map.on_post: command=add_device: failed to add.")
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

if __name__ == "__main__":
    print("Please import file admin.py as a module.")

