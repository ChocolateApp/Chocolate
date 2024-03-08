from typing import List, Callable, Any

EVENTS_MAP: dict[str, List[Callable[[Any], None]]] = {}

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
SERIE_PLAY = "serie_play"

def on(event_name):
    def decorator(handler):
        def wrapper(*args, **kwargs):
            handler(*args, **kwargs)

        if not event_name in EVENTS_MAP:
            EVENTS_MAP[event_name] = []
        event_list = EVENTS_MAP[event_name]
        event_list.append(wrapper)
        return wrapper
    return decorator

def execute_event(event_name, *args, **kwargs):
    from chocolate_app import app
    with app.app_context():
        if event_name in EVENTS_MAP:
            event_list = EVENTS_MAP[event_name]
            for event in event_list:
                event(*args, **kwargs)