'''asgi.py - Entry point for Falcon ASGI app.

Invoke from command line with:
$ uvicorn maps_application.asgi:app

'''

from .app import create_app

app = create_app()

