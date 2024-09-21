from .plugin import StreamDeckPlugin
import asyncio
from pydantic import Field
from typing import Optional

class NextPagePlugin(StreamDeckPlugin):
    async def on_will_appear(self, deck) -> None:
        self.image = "./Assets/next.png"
        self.title=""
        self.update_screen(deck)

    async def on_key_double_click(self, deck) -> None:
        url = 'http://127.0.0.1:8000/admin/lcd_off'
        await self.async_fetch_data(url)
        self.title=""
        self.update_screen(deck)
    
    async def on_key_up(self, deck) -> None:
        url = 'http://127.0.0.1:8000/admin/next'
        await self.async_fetch_data(url)
        self.title=""
        self.update_screen(deck)