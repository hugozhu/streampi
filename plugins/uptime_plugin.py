from .plugin import StreamDeckPlugin
import asyncio

from uptime_kuma_api import UptimeKumaApi
import pandas as pd
from pydantic import Field
from typing import ClassVar

class UptimePlugin(StreamDeckPlugin):
    url: str = Field(default="")
    username: str = Field(default="")
    password: str = Field(default="")

    async def run(self, deck):
        while not self.stop:
            try:
                api = UptimeApi.get_instance(self)
                await asyncio.to_thread(api.login)
            except Exception as e:
                self.error("error in run():", e)

            self.info(api.monitors)
            
            self.update_screen(deck)
            await asyncio.sleep(self.interval)
            
    async def on_will_appear(self, deck) -> None:
        self.update_screen(deck)
        await self.run(deck)

    async def on_key_up(self, deck) -> None:
        await self.update_deck(deck) 


class UptimeApi():
    _instances: ClassVar[dict] = {}
    is_logged_in: bool = False    
    username: str = ""
    password: str = ""
    api: UptimeKumaApi = None
    monitors: pd.DataFrame = None

    def __init__(self, url: str, username: str, password: str, **data):
        super().__init__(**data)
        self.api = UptimeKumaApi(url)   
        self.username = username
        self.password = password

    def login(self):
        if not self.is_logged_in:
            try:
                token = self.api.login(self.username, self.password)
                if "token" in token:
                    self.is_logged_in = True            
                    self.monitors = pd.DataFrame(self.api.get_monitors()).set_index('id')                                       
            except Exception as e:
                print("Failed to login", e)            

    def get_heartbeats(self):
        return self.api.get_heartbeats()

    def get_monitor(self, id):
        return self.api.get_monitor(id)

    def uptime(self):
        return self.api.uptime()


    @staticmethod
    def get_instance(plugin: UptimePlugin):
        if plugin.url not in UptimeApi._instances:
            UptimeApi._instances[plugin.url] = UptimeApi(plugin.url, plugin.username, plugin.password)
        return UptimeApi._instances[plugin.url]