from .plugin import StreamDeckPlugin
import logging
from dingtalk_stream import AckMessage
import dingtalk_stream
from typing import Any
from dingtalkchatbot.chatbot import DingtalkChatbot
import pandas as pd
import asyncio

class EchoMarkdownHandler(dingtalk_stream.ChatbotHandler):
    plugin: Any = None
    deck: Any = None
    
    def __init__(self, logger: logging.Logger = None, plugin = None, deck = None):
        super(dingtalk_stream.ChatbotHandler, self).__init__()          
        self.plugin = plugin
        self.deck = deck

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        self.incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
        text = self.incoming_message.text.content.strip()
        self.plugin.title = text
        self.plugin.image = self.plugin.on_image
        self.plugin.update_screen(self.deck)
        self.reply_markdown('title', text, self.incoming_message)
        return AckMessage.STATUS_OK, 'OK'


class DingtalkPlugin(StreamDeckPlugin):
    client: Any = None
    handler: Any = None
    dingtalk: Any = None
    title: str = ""
    text: str = "Hello World"
    started: bool = False

    access_key: str = ""
    access_secret: str = ""
    access_token: str = ""
    
    on_image: Any = None
    off_image: Any = None

    count: int = 0    
    
    def __init__(self, access_key, access_secret, access_token, **data):
        super().__init__(**data)
        self.off_image = self.image
        self.access_key = access_key
        self.access_secret = access_secret
        self.access_token = access_token
        
    async def receive_incoming_messages(self, deck) -> None:        
        if not self.started:
            self.started = True
            credential = dingtalk_stream.Credential(self.access_key, self.access_secret)
            self.handler = EchoMarkdownHandler(None, self, deck)        
            self.client = dingtalk_stream.DingTalkStreamClient(credential)
            self.client.register_callback_handler(dingtalk_stream.chatbot.ChatbotMessage.TOPIC, self.handler)
            await self.client.start()


    async def on_will_appear(self, deck) -> None:
        await super().on_will_appear(deck)
        self.title = ""
        self.image = self.off_image
        self.background = "black"
        self.update_screen(deck)
        try:
            await self.receive_incoming_messages(deck)
        except Exception as e:
            self.started = False    

    async def on_will_disappear(self, deck) -> None:
        self.started = False
        await super().on_will_disappear(deck)        

    async def on_key_long_pressed(self, deck) -> None:        
        # try:
            # DingTalk.send_markdown(title='Title', text="Hello World")
            # self.handler.reply_markdown(self.title, text=self.text, self.handler.incoming_message)
        # except Exception as e:
        #     print(e)
            
        self.background = "green"
        self.update_screen(deck)
        await asyncio.sleep(0.5)
        self.background = "black"
        self.update_screen(deck)
        
    async def on_key_up(self, deck) -> None:
        global titles
        self.count = self.count + 1
        selected = self.count % len(titles)
        self.title = titles[selected] + "\n\n\n长按发送"
        self.background = "black"
        self.image = self.on_image
        self.update_screen(deck)
