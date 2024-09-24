import os, logging, json
import asyncio
import time

from plugins import StreamDeck, PLUGIN_CLASSES

logger = logging.getLogger("asyncio")

scence_index = 0
deck_keys = [0 for _ in range(32)]
key_press_times = {}
tasks = []
last_key_up_task = None
last_long_press_task = None
DOUBLE_KEY_INTERVAL = 0.3 #seconds
LONG_PRESS_INTERVAL = 1 #seconds

def create_plugin(plugin_type, **kwargs):
    plugin_class = PLUGIN_CLASSES.get(plugin_type)
    if not plugin_class:
        raise ValueError(f"Unknown plugin type: {plugin_type}")
    return plugin_class(**kwargs)

def init_from_json(json_data):
    plugin_global_config = {} #plugin type str -> dict
    plugin_pages = []

    #set up how to show text on key image
    StreamDeck.initialize(config)

    for plugin_config in json_data['plugins']:
        plugin_type = plugin_config.pop("type")
        plugin_global_config[plugin_type] = plugin_config

    for page in json_data['scenes']:
        plugins = []
        for plugin_config in page:
            plugin_type = plugin_config.get("type") or "DummyPlugin"                
            if plugin_type in plugin_global_config:
                plugin_config.update(plugin_global_config[plugin_type])
            plugin = create_plugin(plugin_type, **plugin_config)
            plugins.append(plugin)
        plugin_pages.append(plugins)
    return plugin_pages

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

async def delay_and_key_up(p, deck_keys, key):
    await asyncio.sleep(DOUBLE_KEY_INTERVAL)  # Wait for 0.3 seconds
    await p.on_key_up(deck_keys[key])

async def delay_and_long_press(p, deck_keys, key):
    await asyncio.sleep(LONG_PRESS_INTERVAL)  # Wait for 3 seconds
    print("long press task executed", flush=True)
    await p.on_key_long_pressed(deck_keys[key])

async def key_change_callback(deck, key, state):    
    global scences, scence_index, deck_keys, key_press_times, last_key_up_task, last_long_press_task
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)
    try:
        p = scences[scence_index][key]
        current_time = time.time()
        last_press_time = key_press_times.get(key, 0)
        
        if not state: #key up
            key_press_times[key] = current_time
        
        if not state: #when key up quickly , cancel last long press task
            if last_long_press_task and not last_long_press_task.done():
                print(last_long_press_task, ' long press task cancelled', flush=True)
                last_long_press_task.cancel()
                last_long_press_task = None
        else:
            last_long_press_task = asyncio.create_task(delay_and_long_press(p, deck_keys, key))
            print("long press task created", flush=True)
        
        if current_time - last_press_time < DOUBLE_KEY_INTERVAL and not state: 
            if last_key_up_task and not last_key_up_task.done():
                print(last_key_up_task, ' key up task cancelled')
                last_key_up_task.cancel() 
            asyncio.create_task(p.on_key_double_click(deck_keys[key]))
        
        if not state:
            # keep lcd on
            margins = [0, 0, 0, 0]
            if StreamDeck.lcd_off:
                await dm.set_bright_level(StreamDeck.bright_level)
            else:   
                if last_long_press_task == None:
                    last_key_up_task = asyncio.create_task(delay_and_key_up(p, deck_keys, key))

        else:
            margins = [10, 10, 10, 10]
            asyncio.create_task(p.on_key_down(deck_keys[key]))

        image = deck_keys[key].key_image
        if image:
            image = PILHelper.create_scaled_key_image(deck, image, margins=margins)
            deck.set_key_image(key, PILHelper.to_native_key_format(deck, image))
            
    except Exception as e:
        logger.exception(e)

async def next_page(delta=1):
    global scences, scence_index, deck_keys, tasks
    cancel_tasks()

    for index, p in enumerate(scences[scence_index]):
        asyncio.create_task(p.on_will_disappear(deck_keys[index]))

    scence_index = scence_index + delta
    if scence_index < 0:
        scence_index =  len(scences) - 1

    if scence_index >= len(scences):
        scence_index = 0

    for index, p in enumerate(scences[scence_index]):
        tasks.append(asyncio.create_task(p.on_will_appear(deck_keys[index])))

def cancel_tasks():
    global tasks
    for task in tasks:
        task.cancel()
    tasks = []

async def start():    
    streamdecks = DeviceManager().enumerate()    
    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))
    for index, deck in enumerate(streamdecks):
        
        print(f"Device {index+1} Class Name: {deck.__class__.__name__}, Model Type: {deck.__module__}")
        dm.set_device(deck)
        dm.open()
        dm.set_key_callback_async(key_change_callback)
         
        for index, p in enumerate(scences[scence_index]):
            deck_keys[index] = StreamDeck (
                deck = deck,
                key = index
            )
            task = asyncio.create_task(p.on_will_appear(deck_keys[index]))        
            tasks.append(task)
        return

class DeviceManagerDelegate:
    """
    物理设备的代理类，同时兼容StreamDeck和StreamDock
    """
    deck = None
    def __init__(self, device_model):
        self.device_model = device_model
    
    def import_device_manager(self):
        if self.device_model == 'streamdeck':
            from StreamDeck.DeviceManager import DeviceManager
            from StreamDeck.ImageHelpers import PILHelper
        else:
            from StreamDock.DeviceManager import DeviceManager
            from StreamDock.ImageHelpers import PILHelper
        return DeviceManager, PILHelper

    def get_dervice(self):
        return self.deck

    def set_device(self, deck):
        self.deck = deck

    async def set_bright_level(self, level=0):
        if level == 0:        
            StreamDeck.lcd_off = True
            self.deck.set_brightness(0)
        else:        
            if StreamDeck.lcd_off or level != StreamDeck.bright_level:
                StreamDeck.lcd_off = False
                StreamDeck.set_bright_level(level)
                self.deck.set_brightness(StreamDeck.bright_level)

    def set_key_callback_async(self, key_change_callback):
        self.deck.set_key_callback_async(key_change_callback)

    #唤醒屏幕
    async def screen_on(self):
        if self.deck.__module__.startswith("StreamDock"):
            self.deck.screen_On()
        else:
            await self.set_bright_level(60)
        
    #息屏
    async def screen_off(self):
        if self.deck.__module__.startswith("StreamDock"):
            self.deck.screen_Off()
        else:
            await self.set_bright_level(0)

    #开启      
    def open(self):
        if self.deck:
            # Close deck handle, terminating internal worker threads.
            self.deck.open()
            if self.deck.__module__.startswith("StreamDock"):
                self.deck.set_seconds(60 * 60 * 4)
                self.deck.clearAllIcon()
            else:
                self.deck.reset()
            self.deck.set_brightness(StreamDeck.bright_level)

    #关闭       
    def close(self):
        if self.deck:   
            # Close deck handle, terminating internal worker threads.
            self.deck.close()

config = load_json_file('./config.json')
scences = init_from_json(config)
dm = DeviceManagerDelegate(config.get("device_model"))
DeviceManager, PILHelper = dm.import_device_manager()

if __name__ == "__main__":
    asyncio.run(start())