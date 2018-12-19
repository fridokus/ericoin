from django import template

register = template.Library()


@register.filter
def return_item(lst, i):
    try:
        return lst[i]
    except:
        return None
