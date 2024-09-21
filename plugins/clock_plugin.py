from .plugin import StreamDeckPlugin
import asyncio
import datetime
from math import sin, cos, radians
from pydantic import Field
from typing import Optional
import pytz

def current_time(timezone):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz)    
    return now.hour, now.minute, now.second
        
def generate_clock_svg(hour, minute, second):
    # SVG header
    svg = f'<svg width="200" height="200" viewBox="-100 -100 200 200" xmlns="http://www.w3.org/2000/svg">'
    
    # Clock circle
    svg += f"""
<!-- 圆圈 -->
<circle cx="0" cy="0" r="90" fill="none" stroke="white" stroke-width="6" />

<!-- 整点标记 -->
<line x1="0" y1="-90" x2="0" y2="-80" stroke="white" stroke-width="4" />
<line x1="45" y1="-77.94" x2="40" y2="-69.28" stroke="white" stroke-width="4" />
<line x1="77.94" y1="-45" x2="69.28" y2="-40" stroke="white" stroke-width="4" />
<line x1="90" y1="0" x2="80" y2="0" stroke="white" stroke-width="4" />
<line x1="77.94" y1="45" x2="69.28" y2="40" stroke="white" stroke-width="4" />
<line x1="45" y1="77.94" x2="40" y2="69.28" stroke="white" stroke-width="4" />
<line x1="0" y1="90" x2="0" y2="80" stroke="white" stroke-width="4" />
<line x1="-45" y1="77.94" x2="-40" y2="69.28" stroke="white" stroke-width="4" />
<line x1="-77.94" y1="45" x2="-69.28" y2="40" stroke="white" stroke-width="4" />
<line x1="-90" y1="0" x2="-80" y2="0" stroke="white" stroke-width="4" />
<line x1="-77.94" y1="-45" x2="-69.28" y2="-40" stroke="white" stroke-width="4" />
<line x1="-45" y1="-77.94" x2="-40" y2="-69.28" stroke="white" stroke-width="4" />
"""

    # Hour hand
    hour_angle = 360 * (hour % 12) / 12 + 30 * (minute / 60)
    hour_x = 40 * sin(radians(hour_angle))
    hour_y = -40 * cos(radians(hour_angle))
    svg += f'<line x1="0" y1="0" x2="{hour_x}" y2="{hour_y}" stroke="white" stroke-width="6" />'
    
    # Minute hand
    minute_angle = 360 * minute / 60
    minute_x = 60 * sin(radians(minute_angle))
    minute_y = -60 * cos(radians(minute_angle))
    svg += f'<line x1="0" y1="0" x2="{minute_x}" y2="{minute_y}" stroke="white" stroke-width="4" />'
    
    # Second hand
    second_angle = 360 * second / 60
    second_x = 80 * sin(radians(second_angle))
    second_y = -80 * cos(radians(second_angle))
    svg += f'<line x1="0" y1="0" x2="{second_x}" y2="{second_y}" stroke="yellow" stroke-width="2" />'
    
    # Clock center
    svg += '<circle cx="0" cy="0" r="4" fill="black" />'
    
    # SVG closing tag
    svg += '</svg>'
    
    return svg

async def output(timezone):
    hour, minute, second = current_time(timezone)
    return {
        "image" : generate_clock_svg(hour, minute, second),
        "title": f"{hour:02}:{minute:02}"
    }

class ClockPlugin(StreamDeckPlugin):
    timezone: str = Field(default="Asia/Shanghai")
    count: Optional[int] = 0

    def __init__(self, timezone: str = "Asia/Shanghai",  **data):
        super().__init__(**data)
        self.timezone = timezone

    async def update_deck(self, deck):        
        data = await output(self.timezone)        
        if self.count % 2 == 0:
            self.title = "\n\n\n"+data.get("title","")
            self.image = data["image"]
        else:
            self.title = data.get("title","")+ "\n\n" + self.timezone.replace("/", "\n")
            self.image = None
        self.update_screen(deck)

    async def run(self, deck):
        while not self.stop:
            await self.update_deck(deck)
            await asyncio.sleep(1)
            
    async def on_will_appear(self, deck) -> None:
        await super().on_will_appear(deck)
        await self.run(deck)

    async def on_will_disappear(self, deck) -> None:
        await super().on_will_disappear(deck)
        pass
    
    async def on_key_up(self, deck) -> None:
        self.count = self.count + 1
        await self.update_deck(deck)
        pass