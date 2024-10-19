from typing import List, Optional, Any, ClassVar
from pydantic import BaseModel, ValidationError
from pydantic.fields import Field
from aiocache import cached, Cache
import asyncio 
import httpx, logging
from plugins.streamdeck import StreamDeck

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asyncio")
button_press_times = {}

class TemplateRender:
    def render(template_path : str, context: dict):
        '''
        使用Jinja2模版生成钉钉消息，默认把消息第一行为标题，也可以通过模版变量提取:

        The `template` parameter is a string that represents the path to a Jinja2 template file. This template defines the structure and format of the message that will be sent to DingTalk. It can include placeholders for dynamic content that will be filled in based on the `input` data.

        The `input` parameter is a dictionary containing the data that will be rendered into the template. This data can include various fields such as summary statistics and details about new goods, which will replace the placeholders in the template when generating the final message.

        The function reads the template file, renders it with the provided input data, and returns a dictionary containing the title and the rendered text of the message.
        """
        '''
        import os
        from jinja2 import Environment, FileSystemLoader

        # Define a dictionary to capture the variables
        captured_vars = {}

        # Define a custom filter to capture variable values
        def capture(value, key):
            captured_vars[key] = value
            return value
        
        # 确保模板目录存在
        template_dir = os.path.dirname(template_path)
        env = Environment(loader=FileSystemLoader(template_dir))
        env.filters['capture'] = capture
        
        # 加载模板
        template_name = os.path.basename(template_path)
        template = env.get_template(template_name)
        
        # 渲染模板
        text = template.render(context)
   
        title_value = captured_vars.get('title', 'DingTalk Notification')
        
        return {
            'title': title_value,
            'text': text
        }    

class DataFetcher:
    @staticmethod
    @cached(cache=Cache.MEMORY, ttl=60, namespace="main")
    async def async_fetch_data(url, 
                               post_data=None,                                
                               query_params=None,   
                               headers=None,                               
                               timeout=10,
                               max_retries=2):
        retries = 0
        # print(url, "timeout .....", timeout)
        while retries < max_retries:
            try:
                async with httpx.AsyncClient(headers=headers) as client:                    
                    method = 'POST' if post_data else 'GET'
                    response = await client.request(method,
                                                    url,
                                                    json=post_data,
                                                    params=query_params, 
                                                    timeout=timeout)
                    
                response.raise_for_status()  # Raise an error for bad status codes
                return response.json()
            except Exception as e:
                print(query_params)
                retries += 1                
                logger.error(f"{url} {e}. Retrying ({retries}/{max_retries})...")
                
        return {}
    
    #   urls_with_data = [
    #     {"url": url, "post_data": {"query": stat_ads_spending()}},
    #     {"url": url, "post_data": {"query": stat_new_user()}},
    # ]   
    @staticmethod
    async def fetch_urls(urls_with_data, timeout=10, max_retries=2, headers=None):
        try:
            tasks = [
                DataFetcher.async_fetch_data(url_data['url'], headers=headers, post_data=url_data.get('post_data'), query_params=url_data.get('query_params'), timeout=timeout, max_retries=max_retries)
                for url_data in urls_with_data
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print('fetch_urls', e)
        return [None] * len(urls_with_data)

class StreamDeckPlugin(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    interval: int = 3000 # Default interval set to 3000 seconds    
    image: Any = Field(default=None)
    background: str = "black"
    highlight_color: str = "yellow"
    text_vertical_alignment: str = "center"
    
    margins: List[int] = Field(default_factory=lambda: [0, 0, 0, 0])
    
    data: dict = Field(default_factory=dict)
    stop: bool = False
        
    def base_data_url(self):
        return StreamDeck.base_data_url()

    async def async_fetch_data(self, url, headers=None, post_data=None, query_params=None, timeout=10, max_retries=2):
        return await DataFetcher.async_fetch_data(url, headers=headers, post_data=post_data, query_params=query_params, 
                                                  timeout=timeout, max_retries=max_retries)

    async def fetch_urls(self, urls_with_data, headers=None, timeout=10, max_retries=2):
        return await DataFetcher.fetch_urls(urls_with_data, headers=headers, timeout=timeout, max_retries=max_retries)
    
    
    def info(self, msg, *args, **kwargs):
        logger.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        logger.error(msg, *args, **kwargs)

    def update_screen(self, deck):
        if not self.stop:            
            deck.update_screen(self.title, 
                self.image, 
                self.margins, 
                self.background, 
                self.highlight_color,
                self.text_vertical_alignment)
    
    # event when the plugin start display on key
    async def on_will_appear(self, deck) -> None:
        self.stop = False  # Ensure the event is cleared when appearing  
        pass

    # event when the plugin stop display on key
    async def on_will_disappear(self, deck) -> None:
        self.stop = True  # Signal the event to stop the loop        
        pass

    async def on_key_double_click(self, deck) -> None:
        pass

    async def on_key_long_pressed(self, deck) -> None:
        pass
    
    async def on_key_down(self, deck) -> None:
        pass

    async def on_key_up(self, deck) -> None:
        pass