from .plugin import StreamDeckPlugin

class UptimePlugin(StreamDeckPlugin):
    
    async def on_will_appear(self, deck) -> None:
        await super().on_will_appear(deck)
        self.update_screen(deck)