import time
from io import BytesIO
from typing import Any, ClassVar

import cairosvg
from dingtalkchatbot.chatbot import DingtalkChatbot
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel
from pydantic.fields import Field


class DingTalk:
    @classmethod
    def initialize(cls, config):
        token = config.get("token", "")
        url = f"https://oapi.dingtalk.com/robot/send?access_token=" + token
        cls.dingtalk = DingtalkChatbot(url)

    @staticmethod
    def send_markdown(title, text):
        DingTalk.dingtalk.send_markdown(title=title, text=text, is_at_all=True)


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
            cls.tiny_font = ImageFont.truetype(
                "./Assets/Arial-Unicode-Bold.ttf", config["fonts"]["tiny_font"]
            )
            cls.small_font = ImageFont.truetype(
                "./Assets/Arial-Unicode-Bold.ttf", config["fonts"]["small_font"]
            )
            cls.medium_font = ImageFont.truetype(
                "./Assets/Arial-Unicode-Bold.ttf", config["fonts"]["medium_font"]
            )
            cls.bold_font = ImageFont.truetype(
                "./Assets/Arial-Unicode-Bold.ttf", config["fonts"]["bold_font"]
            )
            cls.max_lines = config.get("max_lines", 4)
            cls._initialized = True


class StreamDeck(BaseModel):
    bright_level: ClassVar[int] = 60
    lcd_off: ClassVar[bool] = False

    deck: Any = Field(default=None)
    key: int
    key_image: Any = Field(default=None)
    data_port: int = 8000

    config: dict = Field(default={})

    @classmethod
    def base_data_url(cls):
        return f"http://127.0.0.1:{StreamDeck.data_port}"

    @classmethod
    def initialize(cls, config):
        StreamDeck.config = config
        StreamDeck.data_port = config.get("server_port", 8000)
        DingTalk.initialize(config["dingtalk"])
        TextSetting.initialize_fonts(config["text_setting"])

    @staticmethod
    def set_bright_level(level=0):
        if level == 0:
            StreamDeck.lcd_off = True
        else:
            StreamDeck.lcd_off = False
            StreamDeck.bright_level = level

    def update_screen(
        self,
        title,
        image,
        margins=[0, 0, 0, 0],
        background="black",
        highlight_color="yellow",
        text_vertical_alignment="center",
    ):
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

            scaled_image = PILHelper.create_scaled_key_image(
                self.deck, icon, margins=margins, background=background
            )
            _draw_text(scaled_image, title, highlight_color, text_vertical_alignment)
            self.deck.set_key_image(
                self.key, PILHelper.to_native_key_format(self.deck, scaled_image)
            )
            self.key_image = scaled_image
        except Exception as e:
            print(e)

    def create_marquee_text(
        self,
        title,
        background="black",
    ):
        # 计算每行文字宽度
        try:
            line_widths = []
            font = TextSetting.medium_font
            for line in title:
                bbox = font.getbbox(line)  # 返回 (x0, y0, x1, y1)
                w = bbox[2] - bbox[0]  # 文字宽度
                line_widths.append(w)

            _create_marquee_text(
                self.deck, self.key, title, line_widths, offsets=[0] * len(title)
            )
        except Exception as e:
            import traceback

            print("Error in create_marquee_text:")
            print(traceback.format_exc())


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
                    lines.extend(
                        [""] * (max_lines - len(lines))
                    )  # Extend with empty strings
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
                f = TextSetting.small_font
                color = highlight_color
                y += f.size
            draw.text((x, y), text=line, font=f, anchor="ms", fill=color)


def _is_svg(svg_string):
    if isinstance(svg_string, str):
        svg_string = svg_string.strip()
        return svg_string.startswith("<") and svg_string.endswith("</svg>")
    return False


TEXT_COLOR = (255, 255, 255)
BG_COLOR = (0, 0, 0)
SCROLL_SPEED = 0.05  # 秒/帧
FONT_SIZE = 20


def _create_marquee_text(deck, key_index, lines, line_widths, offsets):
    # 初始化每行偏移
    from StreamDock.ImageHelpers import PILHelper

    offsets = [0] * len(lines)
    while True:
        img = _create_marquee_image(deck, lines, line_widths, offsets)
        deck.set_key_image(key_index, PILHelper.to_native_key_format(deck, img))
        # 每行文字更新偏移量
        for i in range(len(lines)):
            offsets[i] += 2  # 每帧移动像素
            if offsets[i] >= line_widths[i]:
                offsets[i] = 0
        time.sleep(SCROLL_SPEED)


# 创建跑马灯图像
def _create_marquee_image(deck, lines, line_widths, offsets):
    # key_w, key_h = deck.key_image_size()
    key_w, key_h = (100, 100)
    font = TextSetting.medium_font
    image = Image.new("RGB", (key_w, key_h), color=BG_COLOR)
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(lines):
        offset_x = offsets[i]
        y = i * FONT_SIZE
        # 绘制循环文字
        draw.text((-offset_x, y), line, font=font, fill=TEXT_COLOR)
        if line_widths[i] > key_w:
            draw.text((line_widths[i] - offset_x, y), line, font=font, fill=TEXT_COLOR)
    return image
