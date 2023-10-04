from django import template

register = template.Library()

@register.filter
def replace(value, args):
    search, replace = args.split(',')
    return value.replace(search, replace)
