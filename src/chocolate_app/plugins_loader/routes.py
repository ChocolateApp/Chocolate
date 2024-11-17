import re
import os
import jinja2

from typing import Any, Callable, Dict
from flask import Flask, Response, jsonify, make_response, request, send_file

from chocolate_app import TemplateNotFound, get_dir_path

app = Flask(__name__)

ROUTES: list[tuple[str, str, Callable, list]] = []

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

def new(path: str, methods: list = ["GET"], **kwargs) -> Callable:
    """
    Decorator to create a new route

    Args:
        path (str): The path of the route
        methods (list): The methods of the route (default: ["GET"])
        kwargs: The keyword arguments of the route

    Returns:
        Callable: The decorator
    """

    def decorator(handler):
        file_path = '/'.join(handler.__code__.co_filename.split('/')[:-1]) + "/templates"
        methods = ["GET"]
        if "methods" in kwargs:
            methods = kwargs["methods"]

        ROUTES.append((path, file_path, handler, methods))
        
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

def render_template(template: str, **kwargs) -> str | None:
    """
    Render a template

    Args:
        template (str): The template to render
        args: The arguments of the template
        kwargs: The keyword arguments of the template

    Returns:
        Response: The response of the template
    """
    url_path = request.path
    template_file = None

    for pattern, folder_path, handler, methods  in ROUTES:
        if match_rule(pattern, url_path):
            if os.path.exists(f"{folder_path}/{template}"):
                template_file = template
                break
            else:
                raise TemplateNotFound(f"Template {template} not found in {folder_path}")

    if not template_file:
        return None
    html = ""

    with open(f"{folder_path}/{template_file}", "r") as file:
        html = file.read()

    return jinja2.Template(html).render(kwargs)

def execute_route(path: str, *args, **kwargs) -> Any:
    """
    Execute a route

    Args:
        path (str): The path of the route
        methods (list): The methods of the route (default: ["GET"])
        args: The arguments of the route
        kwargs: The keyword arguments of the route

    Returns:
        Response: The response of the route
    """
    if not path.startswith('/'):
        path = '/' + path

    with app.app_context():
        response = None

        methods = ["GET"]
        if "methods" in kwargs:
            methods = kwargs["methods"]

        for pattern, folder_path, handler, methods in ROUTES:
            if match_rule(pattern, path):
                if request.method not in methods:
                    return make_response("Method not allowed", 405)
                response = handler(*get_attributes(pattern, path), methods=methods, *args, **kwargs)
                try:
                    return response
                except:
                    break

        if isinstance(response, str):
            return send_file(f"{folder_path}/{response}")
        elif isinstance(response, Dict):
            response = jsonify(response)
        elif not isinstance(response, Response):
            response = make_response(response)

        return response


def have_static_file(path: str) -> bool:
    """
    Check if a static file exists

    Args:
        path (str): The path to check

    Returns:
        bool: True if the static file exists, False otherwise
    """
    if path is None:
        return False

    cwd = get_dir_path()

    walk = os.walk(cwd + "/static")

    for folder_path, _, files in walk:
        for file in files:
            file = os.path.join(folder_path, file)
            if file.endswith(path):
                return True

    return False


def get_static_file(path: str) -> Response:
    """
    Get a static file

    Args:
        path (str): The path of the static file

    Returns:
        Response: The response of the static file
    """
    if path is None:
        return make_response("Not found", 404)

    cwd = get_dir_path()

    walk = os.walk(cwd + "/static")

    for folder_path, _, files in walk:
        for file in files:
            file = os.path.join(folder_path, file)
            if file.endswith(path):
                return send_file(file)

    return make_response("Not found", 404)
