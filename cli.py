import os, logging, json
import asyncio
import time

from plugins import StreamDeck, PLUGIN_CLASSES

logger = logging.getLogger("asyncio")

my_deck = None
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
    StreamDeck.initialize(config['text_setting'])

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

config = load_json_file('./config.json')
scences = init_from_json(config)

if config.get("device_model") == 'streamdeck':
    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper
else:
    from StreamDock.DeviceManager import DeviceManager
    from StreamDock.ImageHelpers import PILHelper

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
                await set_bright_level(StreamDeck.bright_level)
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

async def next_page():
    global scences, scence_index, deck_keys, my_deck, tasks

    cancel_tasks()
    
    for index, p in enumerate(scences[scence_index]):
        asyncio.create_task(p.on_will_disappear(deck_keys[index]))

    scence_index = scence_index + 1 if scence_index < len(scences) -1 else 0
    
    for index, p in enumerate(scences[scence_index]):
        tasks.append(asyncio.create_task(p.on_will_appear(deck_keys[index])))

async def set_bright_level(level=0):
    global my_deck
    if level == 0:        
        StreamDeck.lcd_off = True
        my_deck.set_brightness(0)
    else:        
        if StreamDeck.lcd_off or level != StreamDeck.bright_level:
            StreamDeck.lcd_off = False
            StreamDeck.set_bright_level(level)
            my_deck.set_brightness(StreamDeck.bright_level)

def cancel_tasks():
    global tasks
    for task in tasks:
        task.cancel()
    tasks = []

async def start():
    global scences, deck_keys, my_deck, tasks
    
    streamdecks = DeviceManager().enumerate()    
    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))
    for index, deck in enumerate(streamdecks):
        my_deck = deck
        print(f"Device {index+1} Class Name: {deck.__class__.__name__}, Model Type: {deck.__module__}")
        deck.open()
        if deck.__module__.startswith("StreamDock"):
            deck.clearAllIcon()
        else:
            deck.reset()
        deck.set_brightness(StreamDeck.bright_level)
        deck.set_key_callback_async(key_change_callback)
         
        for index, p in enumerate(scences[scence_index]):
            deck_keys[index] = StreamDeck (
                deck = deck,
                key = index
            )
            task = asyncio.create_task(p.on_will_appear(deck_keys[index]))        
            tasks.append(task)
        return

def stop():
    global my_deck 
    if my_deck:   
        # Close deck handle, terminating internal worker threads.
        my_deck.close()

if __name__ == "__main__":
    asyncio.run(start())