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

@register.inclusion_tag('filedetailitem.html', takes_context=True)
def detail_item(context, field_name, heading="Heading", editable=False):
    return {'class': field_name,
            'heading': heading,
            'editing': context['editing'],
            'editable': editable,
            'value': context['file'][field_name],
            }
    
# this is now unused
@register.simple_tag(takes_context=True)
def input_field(context, field_name, value):
    editing = context['editing']
    if editing: return '<input type="text" name="%s" value="%s">' % (field_name, value)
    if not value:
        return '<span class="noentry">(none)</span>'
    return value
