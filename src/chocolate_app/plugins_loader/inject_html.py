from typing import Any, Callable, Dict
from flask import Flask, Response, jsonify, make_response, request, send_file
import re, os
import jinja2
from chocolate_app import ChocolateException

app = Flask(__name__)

JAVASCRIPT_CUSTOM_FUNCTIONS: list[str] = []
INJECTION_LIST: list[tuple[str, str, str]] = []
REPLACE_LIST: list[tuple[str, str, str]] = []

def on(pattern, parentQuerySelector, html):
    """
    Function to inject HTML in a page

    Args:
        pattern (str): The pattern to match
        parentQuerySelector (str): The query selector of the parent element
        html (str): The HTML to inject

    Returns:
        None
    """
    INJECTION_LIST.append((pattern, parentQuerySelector, html))

def replace(pattern, parentQuerySelector, html):
    """
    Function to replace HTML in a page

    Args:
        pattern (str): The pattern to match
        parentQuerySelector (str): The query selector of the parent element
        html (str): The HTML to replace

    Returns:
        None
    """
    REPLACE_LIST.append((pattern, parentQuerySelector, html))

def javascript(js_code: str):
    """
    Function to add custom JS code

    Args:
        js_code (str): A JavaScript function

    Returns:
        None
    """

    regex = re.compile(r"^function\s+\w*\s*\([^)]*\)")
    
    if not regex.match(js_code):
        raise ChocolateException("The JS code must be a function")
    

    JAVASCRIPT_CUSTOM_FUNCTIONS.append(js_code)



def generate_js() -> str:
    """
    Function to generate the JS code to inject the HTML

    Returns:
        str: The JS code
    """

    js_code = ""

    for js in JAVASCRIPT_CUSTOM_FUNCTIONS:
        print(js)
        js_code += js + "\n"

    js_code += """
function matchRule(rule, path) {
    var ruleRegex = new RegExp('^' + rule.replace(/<[^>]+>/g, '[^/]+').replace(/\//g, '\\/') + '$');
    return ruleRegex.test(path);
}

let previousPath = "";
let pagesDone = [];

setInterval(() => {
    if (previousPath !== window.location.pathname) {
"""

    for pattern, parentQuerySelector, html in INJECTION_LIST:
        js_code += f"""
        if (matchRule("{pattern}", window.location.pathname)) {{
            element = document.querySelector("{parentQuerySelector}");
            element.innerHTML += `{html}`;
        }}
        """

    for pattern, parentQuerySelector, html in REPLACE_LIST:
        js_code += f"""
        if (matchRule("{pattern}", window.location.pathname)) {{
            element = document.querySelector("{parentQuerySelector}");
            element.innerHTML = `{html}`;
        }}
        """

    js_code += """
        previousPath = window.location.pathname;
    }
}, 100);
"""

    return js_code
