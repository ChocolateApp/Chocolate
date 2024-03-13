from typing import Any, Callable, Dict
from flask import Flask, Response, jsonify, make_response
import re

app = Flask(__name__)

ROUTES: list[tuple[str, Callable]] = []

def match_rule(rule: str, path: str) -> bool:
    """
    Check if a path matches a rule

    Args:
        rule (str): The rule to check
        path (str): The path to check

    Returns:
        bool: True if the path matches the rule, False otherwise
    """
    rule_regex = re.sub(r'<[^>]+>', r'[^/]+', rule)
    rule_regex = '^' + rule_regex.replace('/', r'\/') + '$'

    return re.match(rule_regex, path) is not None

def new(path: str) -> Callable:
    """
    Decorator to create a new route

    Args:
        path (str): The path of the route

    Returns:
        Callable: The decorator
    """

    def decorator(handler):
        ROUTES.append((path, handler))
        
        @app.route(path)
        def wrapper(*args, **kwargs):
            response = handler(*args, **kwargs)

            if response is None:
                response = make_response('')
            elif not isinstance(response, Response):
                response = make_response(response)

            return response

        return wrapper

    return decorator

def have_route(path: str) -> bool:
    """
    Check if a route exists

    Args:
        path (str): The path to check

    Returns:
        bool: True if the route exists, False otherwise
    """
    if path is None:
        return False

    if not path.startswith('/'):
        path = '/' + path
    
    for rule in ROUTES:
        if match_rule(rule[0], path):
            return True
    
    return False
        
def get_attributes(pattern: str, path: str) -> list:
    """
    Get the attributes of a path

    Args:
        pattern (str): The pattern of the route
        path (str): The path to check

    Returns:
        list: The attributes of the path
    """
    pattern_parts = pattern.split('/')
    path_parts = path.split('/')
    
    attributes = []
    
    for i in range(len(pattern_parts)):
        if pattern_parts[i].startswith('<') and pattern_parts[i].endswith('>'):
            if ":" in pattern_parts[i]:
                attributes.append(pattern_parts[i].split(':')[1][:-1])
            else:
                attributes.append(path_parts[i])
    
    return attributes

def execute_route(path: str, *args, **kwargs) -> Any:
    """
    Execute a route

    Args:
        path (str): The path of the route
        args: The arguments of the route
        kwargs: The keyword arguments of the route

    Returns:
        Response: The response of the route
    """
    if not path.startswith('/'):
        path = '/' + path
    with app.app_context():
        try:
            response = None
            for pattern, handler in ROUTES:
                if match_rule(pattern, path):
                    response = handler(*get_attributes(pattern, path), *args, **kwargs)
                    break
            
            if isinstance(response, Dict):
                response = jsonify(response)
            elif not isinstance(response, Response):
                response = make_response(response)
            return response
        except Exception as e:
            from chocolate_app.utils.utils import log
            log("Error", "Routes", f"An error occurred while executing the route {path}: {str(e)}")
            return make_response('', 404)
