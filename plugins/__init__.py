import os
import importlib
from plugins.streamdeck import StreamDeck

PLUGIN_CLASSES = {}

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

__all__ = [
    "StreamDeck",
    "PLUGIN_CLASSES",
]