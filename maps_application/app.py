import logging
import falcon.asgi
import pathlib
from jinja2 import Environment, PackageLoader, select_autoescape
import json

# Local imports
# from .?? import ??

# Set up logging
logpath = pathlib.Path.cwd() / pathlib.Path("logs")
logpath.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=logpath/"app.log", level=logging.INFO)
logger = logging.getLogger(__name__)

# Templates
# Set up templates
templates_env = Environment(
    loader=PackageLoader("maps_application"),
    autoescape=select_autoescape()
)

class Map:
    def __init__(self):
        self._foo = "Foo!"
    async def on_get(self, req, resp):
        logger.info(f"Map.on_get: Entry with req = {req}.")
        headers = []
        for h in req.scope["headers"]:
            headers.append(h)
        logger.info(f"  headers = {headers}")
        assert req.scope["type"] == "http"

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML
        template = templates_env.get_template("index.html")
        resp.text = template.render({"request": req})


def create_app(config=None):
    # config = config or Config()
    logger.info(f"create_app: Creating new falcon.asgi.App.")

    # store = Store(config)
    # images = Images(config, store)

    app = falcon.asgi.App()
    logger.info(f"create_app: Creating new route /map.")
    app.add_route('/map', Map())
    # app.add_route('/??/{e.g.device{devicenumber}}', ??, suffix='??')

    return app



class ErrorResource:
    async def on_get(self, req, resp):
        raise Exception('Something went wrong!')

