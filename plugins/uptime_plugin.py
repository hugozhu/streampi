from .plugin import StreamDeckPlugin

from uptime_kuma_api import UptimeKumaApi
import pandas as pd
from pydantic import Field
from typing import ClassVar
import asyncio
from datetime import datetime
import traceback 
from fastapi import APIRouter

router = APIRouter(
    prefix="/uptime",
    tags=["plugin"]
)

@router.get("/ok")
async def health_check():
    return "OK"

@router.get("/stop")
async def stop(url: str, monitor_id: int, key_up_count: int):
    api = SingletonUptimeApi.get_instance_by_url(url)
    api.logout()

@router.get("/get_data")
async def get_data(url: str, monitor_id: int, key_up_count: int, interval: int):
    api = SingletonUptimeApi.get_instance_by_url(url)
    if not api.task:
        api.task = AsyncRequester(api._login, interval)
    
    await api.task._first_call_done_event.wait()

    title = "\nLoading..."
    background = "black"
    
    try:
        monitors_df = api.monitors           
        if monitors_df is not None and not monitors_df.empty:
            if monitor_id > 0:
                df = monitors_df[monitors_df['id'] == monitor_id]
                if not df.empty:
                    node = df.iloc[0]
                    # print(node)
                    uptime_in_24 = f"{node.uptime_in_24 * 100:.2f}%"
                    uptime_in_720 = f"{node.uptime_in_720 * 100:.2f}%"
                    down_count = node.down_count
                    ping = f"{node.ping} ms"                      
                    
                    if node.uptime_in_24 < 0.8:
                        background = "red"
                    elif int(node.uptime_in_24) == 1:
                        background = "black"
                    else:
                        background = "#999900"

                    if key_up_count % 2 == 0:
                       title = f"{uptime_in_24}\n{uptime_in_720}\n{node.msg}"
                    else:
                        if pd.isna(node.parent):
                            title = f"{convert_to_multiple_lines(node.msg)}"
                        else:
                            title = f"Ping:\n{ping}\nDown: {down_count}"
                else:
                    title = "\nLoading..."
            else:
                ok_monitors = monitors_df[monitors_df['active'] & (monitors_df['status'] == 1)]                    
                error_monitors = monitors_df[monitors_df['active'] & (monitors_df['status'] == 0) & (monitors_df['parent'].notna())]
                succ_count = len(ok_monitors)
                err_count = len(error_monitors)
                if err_count>0:
                    background = "red"
                else:
                    background = "black"
                if key_up_count % 2 == 0:
                    title = f"Succ: {succ_count}\nErr: {err_count}"
                else:
                    if not error_monitors.empty:
                        node = error_monitors.iloc[0]
                        msg = convert_to_multiple_lines(f"{node.id} {node.msg}")
                    else:
                        msg = "Clean"                            
                    title = f"{msg}"            
    except Exception as e:
        print(e)
        traceback.print_exc()
    
    return {
        "title" : title,
        "background" : background
    }

@router.get("/get_monitors")
async def get_monitors(url):
    api = SingletonUptimeApi.get_instance_by_url(url).api
    return api.get_monitors()

@router.get("/get_heartbeats")
async def get_heartbeats(url: str):
    api = SingletonUptimeApi.get_instance_by_url(url).api
    return api.get_heartbeats()

def convert_to_multiple_lines(text: str, max_lines: int = 4) -> str:
    lines = text.split(" ")
    if len(lines) > max_lines:
        lines = lines[-max_lines:]  # Keep only the last 'max_lines' lines
    return "\n".join(lines)

class UptimePlugin(StreamDeckPlugin):
    url: str = Field(default="")
    monitor_id: int =Field(default=0)
    username: str = Field(default="")
    password: str = Field(default="")
    key_up_count: int = 0

    

    def __init__(self, **data):
        super().__init__(**data)
        SingletonUptimeApi(self)

    async def refresh(self, deck):
        data = await self.async_fetch_data(f"{self.base_data_url()}/uptime/get_data",
                        query_params = {
                            "url": self.url, 
                            "monitor_id": self.monitor_id, 
                            "key_up_count": self.key_up_count,
                            "interval": self.interval
                        }
                    )
        if data:
            self.title = data['title'] + "\n" + self.name
            self.background = data['background']
            self.update_screen(deck)

    async def run(self, deck):        
        while not self.stop:
            await self.refresh(deck)
            await asyncio.sleep(self.interval)
        
        await self.async_fetch_data(f"{self.base_data_url()}/uptime/stop",
                        query_params = {
                            "url": self.url, 
                            "monitor_id": self.monitor_id, 
                            "key_up_count": self.key_up_count
                        }
                    )
            
    async def on_will_appear(self, deck) -> None:
        await super().on_will_appear(deck)
        self.update_screen(deck)
        await self.run(deck)

    async def on_will_disappear(self, deck) -> None:
        await super().on_will_disappear(deck)

    async def on_key_up(self, deck) -> None:
        self.key_up_count = self.key_up_count + 1
        await self.refresh(deck)

class AsyncRequester:
    def __init__(self, func, interval):
        self.func = func
        self._task = asyncio.create_task(self._fetch_periodically(interval))
        self._first_call_done_event = asyncio.Event()

    async def _fetch_periodically(self, interval):
        while True:
            if self.func():
                self._first_call_done_event.set()
                await asyncio.sleep(interval)
            else:
                await asyncio.sleep(10)

    def cancel(self):
        if not self._task.done():
            self._task.cancel()

    def __del__(self):
        self.cancel()

class SingletonUptimeApi:
    '''
    UptimeKumaApi的代理类，和接口交互，接收输入，提供数据给Plugin展示，正常情况下是定时拉取数据并更新
    '''
    _instances: ClassVar[dict] = {}
    is_logged_in: bool = False    
    username: str = ""
    password: str = ""
    api: UptimeKumaApi = None
    monitor_id: int = 0
    monitors: pd.DataFrame = None

    task = None

    def __new__(cls, plugin: UptimePlugin):
        key = plugin.url
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
        return cls._instances[key]    

    def __init__(self, plugin, **kwargs):
        super().__init__(**kwargs)
        self.api = UptimeKumaApi(plugin.url)
        self.username = plugin.username
        self.password = plugin.password
        self.monitor_id = plugin.monitor_id        

    def __del__(self):
        if self.task:
            del self.task

    @staticmethod
    def get_instance_by_url(url: str):
        return SingletonUptimeApi._instances[url]

    def collect_data(self):
        monitors = self.api.get_monitors()        
        uptimes =  self.api.uptime()
        heartbests = self.api.get_heartbeats()

        df_monitors = pd.DataFrame(monitors).set_index('id')
        data = []
        for id, item in uptimes.items():
            uptime_in_24 = item[24]
            uptime_in_720 = item[720]
            monitor = df_monitors.loc[id]
            # status = api.get_monitor_status(id)

            data.append({
                        'id': id,
                        'active': monitor['active'],
                        'parent': monitor['parent'],
                        'name': monitor['name'],
                        'uptime_in_24': uptime_in_24, 
                        'uptime_in_720': uptime_in_720
                        })

        df = pd.DataFrame(data)
        all_monitors = df
        low_uptime_monitors = df[df['uptime_in_24'] < 1]
        low_uptime_monitors = low_uptime_monitors[low_uptime_monitors['parent'].notna()]

        data = []
        
        for id, item in heartbests.items():
            x = item[0]  
            x['id'] = id
            data.append(x)
        df = pd.DataFrame(data)   
        all_heartbeats = df

        merged_df = pd.merge(all_monitors, all_heartbeats, left_on='id', right_on='id', how='left')
        return merged_df

    def _login(self):        
        if not self.is_logged_in:
            try:
                print(f"{ datetime.now() }\t==\tlogin to {self.api.url}")
                token = self.api.login(self.username, self.password)
                if "token" in token:
                    self.is_logged_in = True
            except Exception as e:
                print(f"Failed to login {self.api.url} and collect data :", e)            

        if self.is_logged_in:
            try:                
                print(f"{ datetime.now() }\t==\tcollect_data at {self.api.url}")
                self.monitors = self.collect_data().fillna(0)
                return True
            except Exception as e:
                self.is_logged_in = False
                print("Failed to collect data", e) 

        return False

    def _logout(self):        
        if self.is_logged_in:
            self.is_logged_in = False
            self.api.logout()            

    def get_heartbeats(self):
        return self.api.get_heartbeats()

    def get_monitor(self, id):
        return self.api.get_monitor(id)

    def uptime(self):
        return self.api.uptime()        