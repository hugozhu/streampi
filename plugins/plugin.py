from typing import List, Optional, Any, ClassVar
from pydantic import BaseModel, ValidationError
from pydantic.fields import Field
from aiocache import cached, Cache
import asyncio 
import httpx, logging, time
from plugins.streamdeck import StreamDeck

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asyncio")
button_press_times = {}

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
        return f'http://127.0.0.1:{StreamDeck.data_port}'

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