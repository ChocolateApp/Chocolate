"""A plugin loader"""

import os
import yaml
import importlib

def handle_default(yaml: dict, key: str, default: str = "Unknown") -> str:
    """Handle the default values for the plugin.yaml file"""
    if key not in yaml:
        return default
    else:
        return yaml[key]
    
PLUGIN_FRONTENDS: list[str] = []

def load_plugins(plugins_path: str) -> None:
    """Load plugins from the given path"""
    for folders in os.listdir(plugins_path):
        if os.path.isdir(f"{plugins_path}/{folders}"):
            path = f"{plugins_path}/{folders}"
            yaml_file_path = f"{path}/plugin.yaml"
            if os.path.exists(yaml_file_path):
                with open(yaml_file_path, "r") as yaml_file:
                    plugin = yaml.safe_load(yaml_file)
                    if not plugin:
                        continue
                    plugin_name = handle_default(plugin, "name")
                    plugin_version = handle_default(plugin, "version", "1")
                    plugin_author = handle_default(plugin, "author")
                    plugin_file = handle_default(plugin, "file", "main")

                    plugin_module = os.path.basename(plugin_file).split('.')[0]

                    plugin_file = f"{path}/backend/{plugin_module}.py"
                    from chocolate_app.utils.utils import log

                    plugin_module_name = f"plugin_{plugin_name}"
                    specs = importlib.util.spec_from_file_location(plugin_module_name, plugin_file)
                    if not specs:
                        log("Error", "Plugin Loader", f"Could not load plugin {plugin_name} v{plugin_version} by {plugin_author}\n")
                        continue
                    new_module = importlib.util.module_from_spec(specs)
                    if not specs.loader:
                        log("Error", "Plugin Loader", f"Could not load plugin {plugin_name} v{plugin_version} by {plugin_author}\n")
                        continue

                    from chocolate_app import app
                    with app.app_context():
                        specs.loader.exec_module(new_module)

                    PLUGIN_FRONTENDS.append(f"{path}/frontend")