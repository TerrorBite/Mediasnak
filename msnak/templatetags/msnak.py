from django import template
from django.template.defaultfilters import stringfilter
import urllib

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

@register.simple_tag(takes_context=True)
def get_query(context, field_name, value):
    if 'query' not in context: return urllib.urlencode({field_name: value})
    q = context['query']
    qs = dict([(i, str(q[i])) for i in q]) # not really sure wtf I'm writing any more
    qs.update({field_name: value})         # I just know it works
    return urllib.urlencode(qs)
