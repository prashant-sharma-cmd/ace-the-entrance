from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Usage: {{ my_dict|get_item:key }}"""
    return dictionary.get(key)


@register.filter
def time_display(seconds):
    """Convert integer seconds to mm:ss string."""
    if seconds is None:
        return '--:--'
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m:02d}:{s:02d}"


@register.filter
def mul(value, arg):
    """Multiply value by arg (for CSS conic-gradient)."""
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.simple_tag
def options_list(question):
    """Return list of (index, text) tuples for a question's options."""
    return [
        (1, question.option_1),
        (2, question.option_2),
        (3, question.option_3),
        (4, question.option_4),
    ]