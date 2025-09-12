from django import template
import ast

register = template.Library()

@register.filter
def to_list(value):
    """
    Safely parse a Python-style list string into a real Python list.
    Example: "['yes','cancel']" -> ['yes','cancel']
    """
    if not value:
        return []
    try:
        return ast.literal_eval(value)
    except Exception:
        return []
