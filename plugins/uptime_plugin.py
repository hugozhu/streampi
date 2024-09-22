from .plugin import StreamDeckPlugin
import asyncio

from uptime_kuma_api import UptimeKumaApi
import pandas as pd
from pydantic import Field
from typing import Optional

def fetch_monitor_status():
    pass

class UptimePlugin(StreamDeckPlugin):
    url: str = Field(default="")    
    username: str = Field(default="")
    password: str = Field(default="")

    _instances: dict = {}
    @staticmethod
    def get_uptime_plugin_instance(url, **data):
        if url not in UptimePlugin._instances:
            UptimePlugin._instances[url] = UptimePlugin(**data)
        return UptimePlugin._instances[url]

    def __new__(cls, **data):
        if not hasattr(cls, 'instance'):
            cls.instance = super(UptimePlugin, cls).__new__(cls)
        return cls.instance

    def __init__(self, url: str, username: str, password: str, **data):
        super().__init__(**data)     
        self.url = url
        self.username = username
        self.password = password            
        
    async def run(self, deck):
        while not self.stop:
            # if not self.monitors:
                # login = api.login('hhoroot', 'Hh0_twgdh2024_btzhy!')
                # self.monitors = pd.DataFrame(api.get_monitors()).set_index('id')            
                # print(self.monitors)
                
            self.update_screen(deck)
            await asyncio.sleep(3000)
            
    async def on_will_appear(self, deck) -> None:
        self.update_screen(deck)
        await self.run(deck)

    async def on_will_disappear(self, deck) -> None:
        pass

    async def on_key_up(self, deck) -> None:
        await self.update_deck(deck) 