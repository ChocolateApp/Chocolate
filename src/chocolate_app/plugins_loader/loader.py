"""A plugin loader"""

import os
import importlib
import yaml
import datetime

def log(log_type, log_composant=None, log_message=""):
    the_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"{the_time} - [{log_type}]"
    LOG_PATH = "/var/chocolate/server.log"
    if log_composant:
        log += f" [{log_composant}] {log_message}\n"


    # if file does not exist, create it
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w") as logs:
            logs.write(log)
        return

    with open(LOG_PATH, "r") as logs:
        if log in logs.read():
            return

    with open(LOG_PATH, "a") as logs:
        logs.write(log)


def handle_default(yaml: dict, key: str, default: str = "Unknown") -> str:
    """Handle the default values for the plugin.yaml file"""
    if key not in yaml:
        return default
    else:
        return yaml[key]

def load_plugins(plugins_path: str) -> None:
    """Load plugins from the given path"""
    for folders in os.listdir(plugins_path):
        if os.path.isdir(f"{plugins_path}/{folders}"):
            path = f"{plugins_path}/{folders}"
            yaml_file_path = f"{path}/plugin.yaml"
            if os.path.exists(yaml_file_path):
                with open(yaml_file_path, "r") as yaml_file:
                    plugin = yaml.safe_load(yaml_file)

                    plugin_name = handle_default(plugin, "name")
                    plugin_version = handle_default(plugin, "version", "1")
                    plugin_author = handle_default(plugin, "author")
                    plugin_file = handle_default(plugin, "file", "main")

                    plugin_module = os.path.basename(plugin_file).split('.')[0]

                    plugin_file = f"{path}/{plugin_module}.py"

                    log(f"Loading plugin {plugin_name} v{plugin_version} by {plugin_author}")

                    plugin_module_name = f"plugin_{plugin_name}"
                    specs = importlib.util.spec_from_file_location(plugin_module_name, plugin_file)
                    if not specs:
                        log("Error", "Plugin Loader", f"Could not load plugin {plugin_name} v{plugin_version} by {plugin_author}")
                        continue
                    new_module = importlib.util.module_from_spec(specs)
                    if not specs.loader:
                        log("Error", "Plugin Loader", f"Could not load plugin {plugin_name} v{plugin_version} by {plugin_author}")
                        continue
                    from chocolate_app import app
                    with app.app_context():
                        specs.loader.exec_module(new_module)
