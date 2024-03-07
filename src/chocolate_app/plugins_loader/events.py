from typing import List, Callable, Any

EVENTS_MAP: dict[str, List[Callable[[Any], None]]] = {}

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
    if event_name in EVENTS_MAP:
        event_list = EVENTS_MAP[event_name]
        for event in event_list:
            event(*args, **kwargs)