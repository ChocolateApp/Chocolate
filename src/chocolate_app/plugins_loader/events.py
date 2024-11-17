from enum import Enum
from typing import Callable


class Events(Enum):
    BEFORE_START = "before_start"
    AFTER_START = "after_start"
    NEW_MOVIE = "new_movie"
    NEW_SERIE = "new_serie"
    NEW_SEASON = "new_season"
    NEW_EPISODE = "new_episode"
    NEW_GAME = "new_game"
    NEW_TRACK = "new_track"
    NEW_ALBUM = "new_album"
    NEW_ARTIST = "new_artist"
    NEW_BOOK = "new_book"
    NEW_LIBRARY = "new_library"
    LIBRARY_DELETE = "library_delete"
    SETTINGS_UPDATE = "settings_update"
    USER_DELETE = "user_delete"
    LOGIN = "login"
    MOVIE_PLAY = "movie_play"
    EPISODE_PLAY = "episode_play"
    OTHER_PLAY = "other_play"
    CHUNK_MOVIE_PLAY = "chunk_movie_play"
    CHUNK_EPISODE_PLAY = "chunk_episode_play"
    CHUNK_OTHER_PLAY = "chunk_other_play"


class EventManager:
    def __init__(self):
        self.events_map = {}

    def on(self, event_name: Events):
        def decorator(handler: Callable):
            def wrapper(*args, **kwargs):
                handler(*args, **kwargs)

            if event_name not in self.events_map:
                self.events_map[event_name] = []
            event_list = self.events_map[event_name]
            event_list.append(wrapper)
            return wrapper

        return decorator

    def execute_event(self, event_name: Events, *args, **kwargs):
        if event_name in self.events_map:
            event_list = self.events_map[event_name]
            for event in event_list:
                event(*args, **kwargs)


# Instanciation du gestionnaire d'événements
event_manager = EventManager()
on = event_manager.on
execute_event = event_manager.execute_event
