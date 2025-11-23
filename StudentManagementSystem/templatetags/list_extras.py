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
    """Get item from dictionary, trying both string and int key"""
    if dictionary is None:
        return None
    # Try the key as-is first
    if key in dictionary:
        return dictionary[key]
    # Try as string (JSONField often stores keys as strings)
    if str(key) in dictionary:
        return dictionary[str(key)]
    # Try as int (if key was string but dict has int keys)
    try:
        int_key = int(key)
        if int_key in dictionary:
            return dictionary[int_key]
    except (ValueError, TypeError):
        pass
    return None


@register.filter
def dict_get(d, key):
    """Safe dict lookup in templates"""
    if d is None:
        return []
    return d.get(key, [])
