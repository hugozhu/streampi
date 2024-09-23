from .plugin import StreamDeckPlugin
import asyncio

from uptime_kuma_api import UptimeKumaApi
import pandas as pd
from pydantic import Field
from typing import ClassVar
import asyncio
from datetime import datetime
import traceback 

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

    def display(self, api, deck):
        try:
            monitors_df = api.monitors        
            if monitors_df is not None and not monitors_df.empty:
                if self.monitor_id > 0:
                    df = monitors_df[monitors_df['id'] == self.monitor_id]
                    if not df.empty:
                        node = df.iloc[0]
                        # print(node)
                        uptime_in_24 = f"{node.uptime_in_24 * 100:.2f}%"
                        uptime_in_720 = f"{node.uptime_in_720 * 100:.2f}%"
                        down_count = node.down_count
                        ping = f"{node.ping} ms"                      
                        name = self.name
                        
                        if node.uptime_in_24 < 0.8:
                            self.background = "red"
                        elif int(node.uptime_in_24) == 1:
                            self.background = "black"
                        else:
                            self.background = "#999900"

                        if self.key_up_count % 2 == 0:
                            self.title = f"{uptime_in_24}\n{uptime_in_720}\n{node.msg}\n{name}"
                        else:
                            if pd.isna(node.parent):
                                self.title = f"{convert_to_multiple_lines(node.msg)}\n{name}"
                            else:
                                self.title = f"Ping:\n{ping}\nDown: {down_count}\n{name}"
                    else:
                        self.title = "\nLoading...\n"+self.title
                else:
                    ok_monitors = monitors_df[monitors_df['active'] & (monitors_df['status'] == 1)]                    
                    error_monitors = monitors_df[monitors_df['active'] & (monitors_df['status'] == 0) & (monitors_df['parent'].notna())]
                    succ_count = len(ok_monitors)
                    err_count = len(error_monitors)
                    if err_count>0:
                        self.background = "red"
                    else:
                        self.background = "black"
                    if self.key_up_count % 2 == 0:
                        self.title = f"Succ: {succ_count}\nErr: {err_count}\n{self.name}"
                    else:
                        if not error_monitors.empty:
                            node = error_monitors.iloc[0]
                            msg = convert_to_multiple_lines(f"{node.id} {node.msg}")
                        else:
                            msg = "Clean"                            
                        self.title = f"{msg}\n{self.name}"
            else:
                self.title = "\nLoading...\n"+self.title
        except Exception as e:
            print(e)
            traceback.print_exc() 
            
        self.update_screen(deck)

    async def run(self, deck):
        api = UptimeApi.get_instance(self)                
        while not self.stop:
            try:                
                await api.login_and_gather_data()
                self.display(api, deck)
            except Exception as e:
                self.error("error in run():", e)            
            await asyncio.sleep(self.interval)
            
    async def on_will_appear(self, deck) -> None:
        self.update_screen(deck)
        await self.run(deck)

    async def on_key_up(self, deck) -> None:
        self.key_up_count = self.key_up_count + 1
        self.display(UptimeApi.get_instance(self), deck)

class UptimeApi():
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

    @staticmethod
    def get_instance(plugin: UptimePlugin):
        if plugin.url not in UptimeApi._instances:
            UptimeApi._instances[plugin.url] = UptimeApi(plugin.url, 
                                                        plugin.username, 
                                                        plugin.password, 
                                                        plugin.monitor_id)
        return UptimeApi._instances[plugin.url]

    def __init__(self, url: str, username: str, password: str, monitor_id: int, **data):
        super().__init__(**data)
        self.api = UptimeKumaApi(url)
        self.username = username
        self.password = password
        self.monitor_id = monitor_id

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


    async def login_and_gather_data(self):
        if not hasattr(self, '_last_login_time'):
            self._last_login_time = 0

        loop = asyncio.get_running_loop()
        current_time = loop.time()
        if current_time - self._last_login_time >= 30:
            self._last_login_time = current_time
            # self._login()
            # await asyncio.to_thread(self._login)            
            await loop.run_in_executor(None, self._login)

        while self.monitors is None:
            await asyncio.sleep(2)

    def _login(self):
        print(f"{ datetime.now() }\texpensive call: uptime_api.login")
        if not self.is_logged_in:
            try:
                token = self.api.login(self.username, self.password)
                if "token" in token:
                    self.is_logged_in = True
            except Exception as e:
                print("Failed to login and collect data", e)            

        if self.is_logged_in:
            try:                
                self.monitors = self.collect_data()
            except Exception as e:
                self.is_logged_in = False
                print("Failed to collect data", e)

    def get_heartbeats(self):
        return self.api.get_heartbeats()

    def get_monitor(self, id):
        return self.api.get_monitor(id)

    def uptime(self):
        return self.api.uptime()

        