import asyncio

from .plugin import StreamDeckPlugin


class BtcPlugin(StreamDeckPlugin):
    key_up_count: int = 0
    proxy: str = ""
    token: str = ""

    def __init__(self, proxy: str = "", token: str = "", **data):
        super().__init__(**data)
        self.proxy = proxy
        self.token = token

    async def fetch_btc_data(self):
        url = "https://api.blockchain.com/v3/exchange/tickers/BTC-USDT"
        return await self.async_fetch_data(
            url,
            proxy=self.proxy,
            headers={
                "Accept": "application/json",
                "X-API-Token": self.token,
            },
        )

    async def update_deck(self, deck):
        self.update_screen(deck)
        data = await self.fetch_btc_data()
        if data:
            # print(data)
            if self.key_up_count % 2 == 0:
                self.title = f"{int(data['last_trade_price'])} $\n\n24H:\n{int(data['price_24h'])} $"
            else:
                self.title = f"\n{data['symbol']}\n\nVolume 24H:\n{data['volume_24h']}"
            self.update_screen(deck)

    async def run(self, deck):
        while not self.stop:
            await self.update_deck(deck)
            await asyncio.sleep(self.interval)

    async def on_will_appear(self, deck) -> None:
        self.update_screen(deck)
        await self.run(deck)

    async def on_will_disappear(self, deck) -> None:
        pass

    async def on_key_up(self, deck) -> None:
        self.key_up_count = self.key_up_count + 1
        await self.update_deck(deck)
