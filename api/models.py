from __future__ import annotations

import json
import random
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from redis import asyncio as aioredis

if TYPE_CHECKING:
    from typing_extensions import Self


App = Dict[str, Any]


class Universal_DB:
    __slots__ = ("cache", "integrity")

    def __init__(self, cache: List[App], integrity: datetime) -> None:
        self.cache: List[App] = cache
        self.integrity: datetime = integrity

    def get_app_names(self, console: str) -> List[str]:
        return [app['title'] for app in self.cache if app['console'] == console]

    def get_app(self, console: str, application: str) -> Optional[App]:
        for app in self.cache:
            if app['title'] == application and app['console'] == console:
                return app
        return None

    def get_random_app(self, console: str) -> App:
        apps = []
        for app in self.cache:
            if app['console'] == console:
                apps.append(app)
        return random.choice(apps)

    @classmethod
    async def from_redis(cls, pool: aioredis.Redis) -> Self:
        integrity = await pool.get("udb:integrity")
        cache = await pool.get("udb:cache")
        cache = json.loads(cache)
        return cls(cache, datetime.fromisoformat(integrity))
