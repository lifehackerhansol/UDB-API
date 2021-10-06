"""
Copyright 2021-2022 LightSage

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import annotations

import asyncio
import json

from redis import asyncio as aioredis
import sentry_sdk
from fastapi import FastAPI
from jinja2 import Environment, FileSystemLoader
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.responses import HTMLResponse

from .models import Universal_DB
from .routers import add_routers
from .utils import log_exception, setup_redis

try:
    import uvloop  # type: ignore
except ModuleNotFoundError:
    pass
else:
    uvloop.install()


class App(FastAPI):
    redis: aioredis.Redis


app = App(title="TWLMenu-extras", version="1.1.0", docs_url='/swagger-docs', redoc_url=None)
app.add_middleware(SentryAsgiMiddleware)
jinja_env = Environment(loader=FileSystemLoader('templates'), enable_async=True)
add_routers(app)


async def udb_cache_loop():
    while True:
        # There's no reason why integrity and cache should not exist...
        app.state.cache = await Universal_DB.from_redis(app.redis)
        await asyncio.sleep(600)


@app.on_event("startup")
async def on_startup() -> None:
    with open("config.json") as fp:
        config = json.load(fp)

    sentry_sdk.init(config['SENTRY_DSN'],
                    traces_sample_rate=config['SENTRY_SAMPLES_RATE'])

    app.redis = await setup_redis(config['REDIS'])

    task = asyncio.create_task(udb_cache_loop())
    task.add_done_callback(log_exception)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await app.redis.close()


@app.get("/docs", include_in_schema=False)
async def docs():
    html = f"""<!doctype html> <!-- Important: must specify -->
<html>
<head>
  <meta charset="utf-8"> <!-- Important: rapi-doc uses utf8 characters -->
  <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
  <meta name="title" content="TWLMenu-extras API">
  <meta name="author" content="lifehackerhansol">
  <meta property="og:title" content="TWLMenu-extras API">
  <meta property="og:type" content="website">
  <meta property="og:description" content="An actual Universal DB API, modified for TWLMenu-extras">
  <meta property="og:url" content="https://twlmenu-extras.lifehacker101.net">
  <meta property="og:image" content="">
  <title>TWLMenu-extras API</title>
</head>
<body>
  <rapi-doc
    spec-url="{app.openapi_url}"
    theme = "light"
    render-style = "read"
    show-method-in-nav-bar = "as-colored-text"
  > </rapi-doc>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/", include_in_schema=False)
async def home():
    tmpl = jinja_env.get_template("home.html")
    rendered = await tmpl.render_async()
    return HTMLResponse(rendered)
