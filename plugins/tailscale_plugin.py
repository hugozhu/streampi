import asyncio
import logging
from datetime import datetime, timezone

from .plugin import StreamDeckPlugin

logger = logging.getLogger("asyncio")


class TailscalePlugin(StreamDeckPlugin):
    key_up_count: int = 0
    api_key: str = ""
    bg_image: str = ""

    def __init__(self, api_key: str = "", **data):
        super().__init__(**data)
        self.bg_image = self.image
        self.api_key = api_key

    async def fetch_data(self):
        url = "https://api.tailscale.com/api/v2/tailnet/-/devices"
        return await self.async_fetch_data(url, auth=(self.api_key, ""))

    async def update_deck(self, deck):
        self.update_screen(deck)
        data = await self.fetch_data()
        if data:
            # print(data)
            devices = data["devices"]
            today = datetime.now(timezone.utc)
            result = [
                {
                    "name": d.get("name").split(".")[0],
                    "version": d.get("clientVersion").split("-")[0],
                    "expires": (
                        datetime.fromisoformat(d.get("expires").replace("Z", "+00:00"))
                        - today
                    ).days,
                    "expires_enabled": not d.get("keyExpiryDisabled"),
                    "connected": d.get("connectedToControl"),
                }
                for d in devices
                if d.get("connectedToControl") is True
            ]

            total = len(result)
            index = self.key_up_count % len(result)
            if index:
                # 根据 key_up_count 循环取出对应的 item
                current_item = result[index]
                device_name = current_item["name"]
                device_version = current_item["version"]
                expires_days = current_item["expires"]
                expires_enabled = current_item["expires_enabled"]
                if expires_enabled:
                    expire_info = f"{expires_days}d"
                else:
                    expire_info = "no exp"

                self.title = (
                    f"{expire_info}\n{device_version}\n{device_name}\n{index}/{total}"
                )
                self.image = None
            else:
                self.image = self.bg_image
                self.title = f"\n\n{total}"

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
