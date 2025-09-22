import ast

from django import template

register = template.Library()

@register.filter
def to_list(value):
    if not value:
        return []
    try:
        return ast.literal_eval(value)
    except Exception:
        return []

@register.simple_tag
def zip_lists(list1, list2):
    """Zip two lists together for template iteration."""
    return zip(list1, list2)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])

@register.filter
def dict_get(d, key):
    """Safe dict lookup in templates"""
    if d is None:
        return []
    return d.get(key, [])