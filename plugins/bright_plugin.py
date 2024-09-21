from .plugin import StreamDeckPlugin
import asyncio
from pydantic import Field
from typing import Optional

level: int = 60
class BrightPlugin(StreamDeckPlugin):
    step: int = 10
    
    async def on_will_appear(self, deck) -> None:
        await super().on_will_appear(deck)
        self.update_screen(deck)

    async def on_key_up(self, deck) -> None:
        global level
        level = level + self.step
        if level <= 10:
            level = 10
        if level >= 100:
            level = 100

        deck.set_bright_level(level)
        deck.deck.set_brightness(level)
        self.update_screen(deck)