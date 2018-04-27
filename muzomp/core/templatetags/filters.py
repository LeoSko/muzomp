from urllib.parse import unquote

from django import template

register = template.Library()


@register.filter(name="unquote")
def unquote_url(value):
    return unquote(value)


@register.filter(name="duration")
def duration(td, string_format):
    total_seconds = 0
    if isinstance(td, float):
        total_seconds = round(td)
    if hasattr(td, "total_seconds"):
        if callable(td.total_seconds):
            total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = (total_seconds - (hours * 3600 + minutes * 60))

    res = string_format
    if hours < 10:
        res = res.replace("H", "0" + str(hours))
    else:
        res = res.replace("H", str(hours))
    res = res.replace("h", str(hours))

    if minutes < 10:
        res = res.replace("i", "0" + str(minutes))
    else:
        res = res.replace("i", str(minutes))

    if seconds < 10:
        res = res.replace("s", "0" + str(seconds))
    else:
        res = res.replace("s", str(seconds))

    return res.replace("S", str(total_seconds))

