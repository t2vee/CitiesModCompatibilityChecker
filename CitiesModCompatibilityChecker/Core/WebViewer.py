from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
import threading
import uvicorn

templates = Jinja2Templates(directory="templates")

class FastAPISettings:
    def __init__(self):
        self.api_version = "v1"
        self.api_name = "my_api"
        self.db = "some db"
        self.logger = "configured logger"
        self.DEBUG = True


class FastAPIWebReportViewer:
    def __init__(self, settings):
        self.settings = settings
        self._fastapi = FastAPI(
            version=self.settings.api_version,
        )
        self._fastapi.add_api_route(
            path="/keepalive",
            endpoint=self.keepalive,
            methods=["GET"]
        )
        self._fastapi.add_api_route(
            path="/WebReportViewer",
            endpoint=self.web_viewer,
            methods=["GET"]
        )

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    async def keepalive(self, request: Request):
        return {"message": "server is running!",
                "referer": f"{request.client.host}:{request.client.port}" if request.client.port else request.client.host}

    async def web_viewer(self):
        with open(str(config.get('ProgramFiles', 'json_report').replace("./", f"{config_path}/")), 'r') as f:
            json_data = f.read()
            return

    def __getattr__(self, attr):
        if hasattr(self._fastapi, attr):
            return getattr(self._fastapi, attr)
        else:
            raise AttributeError(f"{attr} not exist")

    async def __call__(self, *args, **kwargs):
        return await self._fastapi(*args, **kwargs)

    def run(self):
        while True:
            uvicorn.run(self._fastapi, host="127.0.0.1", port=8000)