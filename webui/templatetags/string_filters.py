# webui/templatetags/string_filters.py

from django import template

register = template.Library()

@register.filter
def strip_whitespace(value):
    """移除字符串首尾空白字符"""
    if value is None:
        return ""
    return str(value).strip()