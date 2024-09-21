from .plugin import StreamDeckPlugin

class DummyPlugin(StreamDeckPlugin):
    
    async def on_will_appear(self, deck) -> None:
        await super().on_will_appear(deck)
        self.update_screen(deck)