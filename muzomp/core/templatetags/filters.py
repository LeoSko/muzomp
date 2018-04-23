from urllib.parse import unquote

from django import template

register = template.Library()


@register.filter(name="unquote")
def unquote_url(value):
    return unquote(value)
