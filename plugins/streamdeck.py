from pydantic import BaseModel
from pydantic.fields import Field
from typing import Any, ClassVar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

import cairosvg

small_font = ImageFont.truetype("./Assets/Arial-Unicode.ttf", 13)
medium_font = ImageFont.truetype("./Assets/Arial-Unicode-Bold.ttf", 14)
bold_font = ImageFont.truetype("./Assets/Arial-Unicode-Bold.ttf", 18)

class StreamDeck(BaseModel):
    bright_level: ClassVar[int] = 60 
    lcd_off: ClassVar[bool] = False

    deck: Any = Field(default=None)
    key: int
    key_image: Any = Field(default=None)

    @staticmethod
    def set_bright_level(level=0):
        if level == 0:
            StreamDeck.lcd_off = True
        else:
            StreamDeck.lcd_off = False
            StreamDeck.bright_level = level

    def update_screen(self, title, image, margins=[0, 0, 0, 0], background="black", highlight_color="yellow"):
        self.key_image = self.draw_svg_text(image, title, margins=margins, background=background, highlight_color=highlight_color)
    
    def draw_svg_text(self, svg_data, label_text="", margins=[0, 0, 0, 0], background="black", highlight_color="yellow"):
        if not svg_data:
            svg_data = '<svg width="400" height="400"></svg>'
            
        try:
            if _is_svg(svg_data):
                png_data = cairosvg.svg2png(bytestring=svg_data)
                icon = Image.open(BytesIO(png_data)) 
            else:
                icon = Image.open(svg_data)
            
            image = PILHelper.create_scaled_key_image(self.deck, icon, margins=margins, background=background)
            _draw_text(image, label_text, highlight_color)
            self.deck.set_key_image(self.key, PILHelper.to_native_key_format(self.deck, image))
            return image
        except Exception as e:
            print(e)

def _draw_text(image, label_text, highlight_color):
        draw = ImageDraw.Draw(image)
        y = 0
        if label_text:
            for index, line in enumerate(label_text.split('\n')):
                # _, _, text_width, text_height = draw.textbbox((0, 0), label_text, font=font)
                x = (image.width) // 2
                color = "white"
                if index == 0:
                    y += 18
                    f = bold_font
                elif index == 1:
                    y += 16
                    f = medium_font            
                elif index == 2:
                    y += 14
                    f = small_font
                elif index == 3:
                    y += 14
                    color = highlight_color
                    f = small_font           
                else:
                    y += 10
                    f = medium_font
                # Draw the text centered
                draw.text((x, y), text=line, font=f, anchor="ms", fill=color)
    
def _is_svg(svg_string):
    if isinstance(svg_string, str):
        svg_string = svg_string.strip()
        return svg_string.startswith('<svg') and svg_string.endswith('</svg>')
    return False