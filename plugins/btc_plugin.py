from .plugin import StreamDeckPlugin
import asyncio

class BtcPlugin(StreamDeckPlugin):
    def __init__(self, **data):
        super().__init__(**data)
        self.image = "./Assets/btc.png"
    
    async def fetch_btc_data(self):
        url = 'https://api.blockchain.com/v3/exchange/tickers/BTC-USD'
        return await self.async_fetch_data(url)

    async def update_deck(self, deck):
        self.update_screen(deck)
        data = await self.fetch_btc_data()
        if data:
            self.title = f"{int(data['last_trade_price'])} $\n\n24H:\n{int(data['price_24h'])} $"
            self.update_screen(deck)

    async def run(self, deck):
        while not self.stop:
            await self.update_deck(deck)
            await asyncio.sleep(3000)
            
    async def on_will_appear(self, deck) -> None:
        self.update_screen(deck)
        await self.run(deck)

    async def on_will_disappear(self, deck) -> None:
        pass

    async def on_key_up(self, deck) -> None:
        await self.update_deck(deck) 