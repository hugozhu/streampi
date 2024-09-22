from .plugin import StreamDeckPlugin
import asyncio

from uptime_kuma_api import UptimeKumaApi
import pandas as pd
from pydantic import Field
from typing import ClassVar, Optional

class UptimeApi():
    _instances: ClassVar[dict] = {}

    @staticmethod
    def get_instance(url, username: str, password: str):
        if url not in UptimeApi._instances:
            UptimeApi._instances[url] = UptimeKumaApi(url)
            UptimeApi._instances[url].login(username,password)
        return UptimeApi._instances[url]

class UptimePlugin(StreamDeckPlugin):
    url: str = Field(default="")
    username: str = Field(default="")
    password: str = Field(default="")

    def __init__(self, url: str, username: str, password: str, **data):
        super().__init__(**data)
        self.url = url
        self.username = username
        self.password = password

    async def run(self, deck):
        while not self.stop:
            # api = UptimeApi.get_instance(self.url, self.username, self.password)
            # df = pd.DataFrame(api.get_monitors()).set_index('id')            
            # print(df)
            self.update_screen(deck)
            await asyncio.sleep(3000)
            
    async def on_will_appear(self, deck) -> None:
        self.stop = False
        self.update_screen(deck)
        await self.run(deck)

    async def on_will_disappear(self, deck) -> None:
        pass

    async def on_key_up(self, deck) -> None:
        await self.update_deck(deck) 