from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def download_url(value):
    return '/download?fileid='+value

@register.filter
@stringfilter
def thumbnail_url(value):
    return '/thumb?fileid='+value

@register.filter
def edit(value):
    if value: return 'false'
    return 'true'
