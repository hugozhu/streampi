import os
import importlib
from plugins.streamdeck import StreamDeck as StreamPi

PLUGIN_CLASSES = {}
PLUGIN_ROUTERS = {}

def convert_to_camel_case(s: str) -> str:
    parts = s.split('_')
    return ''.join(part.capitalize() for part in parts)

# Scan current folder for plugins
for filename in os.listdir(os.path.dirname(__file__)):
    if filename.endswith("_plugin.py"):            
        module_name = filename[:-3]  # Remove the '.py' extension
        module = importlib.import_module(f"plugins.{module_name}", package=__name__)
        plugin_class_name = convert_to_camel_case(module_name)
        plugin_class = getattr(module, plugin_class_name, None)
        if plugin_class:
            print("Loading streampi plugin: ", plugin_class_name, plugin_class)
            PLUGIN_CLASSES[plugin_class_name] = plugin_class
            
        if hasattr(module, 'router'):
            PLUGIN_ROUTERS[plugin_class_name] = module.router

__all__ = [
    "StreamPi",
    "PLUGIN_CLASSES",
    "PLUGIN_ROUTERS"
]