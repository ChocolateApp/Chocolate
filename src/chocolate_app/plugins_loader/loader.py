"""A plugin loader"""

import os
import importlib
import yaml

import sys
sys.path.append("..")

def log(*args):
    """Log to the server.log file"""
    with open("/var/chocolate/server.log", "a") as logs:
        logs.write(" ".join(args) + "\n")

from . import events

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
            yaml_file = f"{plugins_path}/{folders}/plugin.yaml"
            if os.path.exists(yaml_file):
                with open(yaml_file, "r") as yaml_file:
                    plugin = yaml.safe_load(yaml_file)

                    plugin_name = handle_default(plugin, "name")
                    plugin_version = handle_default(plugin, "version", "1")
                    plugin_author = handle_default(plugin, "author")
                    plugin_file = handle_default(plugin, "file", "main")

                    plugin_module = os.path.basename(plugin_file).split('.')[0]

                    plugin_file = f"{plugins_path}/{folders}/{plugin_module}.py"

                    log(f"Loading plugin {plugin_name} v{plugin_version} by {plugin_author}")

                    plugin_module_name = f"plugin_{plugin_name}"
                    specs = importlib.util.spec_from_file_location(plugin_module_name, plugin_file)
                    new_module = importlib.util.module_from_spec(specs)
                    specs.loader.exec_module(new_module)

                    PLUGIN_EVENT_MAP = {
                        "on_movie_play": events.ON_MOVIE_PLAY_FUNCTIONS,
                        "on_serie_play": events.ON_SERIE_PLAY_FUNCTIONS,
                        "on_music_play": events.ON_MUSIC_PLAY_FUNCTIONS,
                        "on_game_play": events.ON_GAME_PLAY_FUNCTIONS,
                        "on_book_read": events.ON_BOOK_READ_FUNCTIONS,
                        "on_login": events.ON_LOGIN_FUNCTIONS,
                        "on_logout": events.ON_LOGOUT_FUNCTIONS,
                        "on_new_movie": events.ON_NEW_MOVIE_FUNCTIONS,
                        "on_new_serie": events.ON_NEW_SERIE_FUNCTIONS,
                        "on_new_season": events.ON_NEW_SEASON_FUNCTIONS,
                        "on_new_episode": events.ON_NEW_EPISODE_FUNCTIONS,
                        "on_new_music_title": events.ON_NEW_MUSIC_TITLE_FUNCTIONS,
                        "on_new_artist": events.ON_NEW_ARTIST_FUNCTIONS,
                        "on_new_album": events.ON_NEW_ALBUM_FUNCTIONS,
                        "on_new_game": events.ON_NEW_GAME_FUNCTIONS,
                        "on_new_book": events.ON_NEW_BOOK_FUNCTIONS,
                        "on_new_user": events.ON_NEW_USER_FUNCTIONS,
                        "on_new_library": events.ON_NEW_LIBRARY_FUNCTIONS,
                        "on_settings_change": events.ON_SETTINGS_CHANGE_FUNCTIONS,
                        "on_user_delete": events.ON_USER_DELETE_FUNCTIONS,
                        "on_library_delete": events.ON_LIBRARY_DELETE_FUNCTIONS,
                        "on_movie_edit": events.ON_MOVIE_EDIT_FUNCTIONS,
                        "on_serie_edit": events.ON_SERIE_EDIT_FUNCTIONS
                    }

                    for event, event_list in PLUGIN_EVENT_MAP.items():
                        if event in plugin:
                            func_to_call = getattr(new_module, plugin[event])
                            event_list.append(func_to_call)