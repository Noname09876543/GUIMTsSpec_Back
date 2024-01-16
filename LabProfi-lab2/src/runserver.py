import os
import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config
from watchfiles import run_process
from django.core.asgi import get_asgi_application
from django.core.management import call_command

# from .custom_logging import create_logger

class Hypercorn:
    bind_ip = '0.0.0.0'
    bind_port = 8080


def runserver():
    # logger = create_logger('./logging_config.yml')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    config = Config()
    config.bind = [
        f'{Hypercorn.bind_ip}:{Hypercorn.bind_port}']
    app = get_asgi_application()
    call_command('migrate')
    asyncio.run(serve(app, config))


if __name__ == "__main__":
    run_process('./', target=runserver)