from pydantic import BaseModel
from pydantic.fields import Field
from typing import Any, ClassVar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import cairosvg

class TextSetting:
    _initialized = False
    tiny_font = None
    small_font = None
    medium_font = None
    bold_font = None
    max_lines = 0

    @classmethod
    def initialize_fonts(cls, config):
        if not cls._initialized:
            cls.tiny_font = ImageFont.truetype("./Assets/Arial-Unicode-Bold.ttf", config['fonts']['tiny_font'])
            cls.small_font = ImageFont.truetype("./Assets/Arial-Unicode-Bold.ttf", config['fonts']['small_font'])
            cls.medium_font = ImageFont.truetype("./Assets/Arial-Unicode-Bold.ttf", config['fonts']['medium_font'])
            cls.bold_font = ImageFont.truetype("./Assets/Arial-Unicode-Bold.ttf", config['fonts']['bold_font'])
            cls.max_lines = config.get("max_lines", 4)
            cls._initialized = True

class StreamDeck(BaseModel):
    bright_level: ClassVar[int] = 60 
    lcd_off: ClassVar[bool] = False

    deck: Any = Field(default=None)
    key: int
    key_image: Any = Field(default=None)

    @classmethod
    def initialize(cls, config):
        TextSetting.initialize_fonts(config)    

    @staticmethod
    def set_bright_level(level=0):
        if level == 0:
            StreamDeck.lcd_off = True
        else:
            StreamDeck.lcd_off = False
            StreamDeck.bright_level = level

    def update_screen(self, title, image, margins=[0, 0, 0, 0], 
                    background="black", 
                    highlight_color="yellow", 
                    text_vertical_alignment="center"):
        if not image:
            image = '<svg width="400" height="400"></svg>'
        
        try:
            if _is_svg(image):
                png_data = cairosvg.svg2png(bytestring=image)
                icon = Image.open(BytesIO(png_data)) 
            else:
                icon = Image.open(image)
                        
            if self.deck.__module__.startswith("StreamDock"):
                from StreamDock.ImageHelpers import PILHelper
            else:
                from StreamDeck.ImageHelpers import PILHelper

            scaled_image = PILHelper.create_scaled_key_image(self.deck, icon, margins=margins, background=background)
            _draw_text(scaled_image, title, highlight_color, text_vertical_alignment)
            self.deck.set_key_image(self.key, PILHelper.to_native_key_format(self.deck, scaled_image))
            self.key_image = scaled_image
        except Exception as e:
            print(e)

def _draw_text(image, label_text, highlight_color, text_vertical_alignment="center"):
        draw = ImageDraw.Draw(image)        
        y = 0
        if label_text:
            lines = label_text.split("\n")
            if text_vertical_alignment == "center":
                max_lines = TextSetting.max_lines
                if max_lines > 0:
                    if len(lines) < max_lines:
                        x = lines.pop()
                        lines.extend([""] * (max_lines - len(lines)))  # Extend with empty strings
                        lines[-1] = x                
                    else:
                        lines = lines[-max_lines:]  # Keep only the last 5 lines 
   
            for index, line in enumerate(lines):
                x = (image.width) // 2
                color = "white"
                if index == 0:
                    f = TextSetting.bold_font
                    y += f.size                    
                elif index == 1:                    
                    f = TextSetting.medium_font            
                    y += f.size 
                elif index == 2:
                    f = TextSetting.small_font
                    y += f.size
                elif index == 3:
                    f = TextSetting.tiny_font
                    color = highlight_color
                    y += f.size
                elif index == 4:
                    color = highlight_color
                    y += f.size                    
                else:
                    f = TextSetting.tiny_font
                    color = highlight_color
                    y += f.size
                draw.text((x, y), text=line, font=f, anchor="ms", fill=color)
    
def _is_svg(svg_string):
    if isinstance(svg_string, str):
        svg_string = svg_string.strip()
        return svg_string.startswith('<') and svg_string.endswith('</svg>')
    return False