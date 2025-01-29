from .plugin import StreamDeckPlugin
import asyncio
import datetime

class GoldPlugin(StreamDeckPlugin):
    key_up_count: int = 0    
    app_key: str = ""

    def __init__(self, app_key: str = "", **data):
        super().__init__(**data)
        self.app_key = app_key
    
    async def fetch_data(self):
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')        
        url = f'https://api.jisuapi.com/gold/storegold?appkey={self.app_key}&date={yesterday}'
        return await self.async_fetch_data(url)

    async def update_deck(self, deck):
        self.update_screen(deck)
        data = await self.fetch_data()
        if data:
            # print(data)
            result = data['result']['list']
            if self.key_up_count % 2 ==0:
                first_item = result[0] if result else None
            else:
                first_item = result[7] if result else None
            if first_item:
                self.title = f"{first_item['gold']}\n\n昨日金价\n{first_item['store_name']}"
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