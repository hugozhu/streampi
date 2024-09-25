from .plugin import StreamDeckPlugin
from . import StreamPi
from pydantic import Field
from typing import Optional

class NextPagePlugin(StreamDeckPlugin):
    prev: str = Field(default=False)    
    def __init__(self, prev: bool = False,  **data):
        super().__init__(**data)
        self.prev = prev
        
    async def on_will_appear(self, deck) -> None:        
        if self.prev:
            self.image = "./Assets/left-arrow.png"
        else:
            self.image = "./Assets/right-arrow.png"
        self.title=""
        self.update_screen(deck)

    async def on_key_double_click(self, deck) -> None:
        url = f'{self.base_data_url()}/admin/lcd_off'
        await self.async_fetch_data(url)
        self.title=""
        self.update_screen(deck)
    
    async def on_key_up(self, deck) -> None:
        if self.prev:
            url = f'{self.base_data_url()}/admin/prev'
        else:
            url = f'{self.base_data_url()}/admin/next'
        await self.async_fetch_data(url)
        self.title=""
        self.update_screen(deck)
