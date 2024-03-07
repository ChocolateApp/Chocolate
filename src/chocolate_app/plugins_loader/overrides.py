from typing import List, Callable, Any

OVERRIDE_MAP: dict[str, Callable[[Any], None]] = {}

def have_override(override_name):
    return override_name in OVERRIDE_MAP


def link(override_name):
    def decorator(handler):
        def wrapper(*args, **kwargs):
            handler(*args, **kwargs)
        OVERRIDE_MAP[override_name] = wrapper
    return decorator

def execute_override(override_name, *args, **kwargs):
    return OVERRIDE_MAP[override_name](*args, **kwargs)