import time
from datetime import datetime
from django import template
from django.db.models.fields import DateTimeField

register = template.Library()

def traverse_object(obj, fieldspec):
    """Traverses a Django model double underscore fieldpath

    Example::
        >>> traverse_object(person, 'group__foo')
        (group, 'foo')
    """
    parts = fieldspec.split('__')
    field = parts[-1]
    for part in parts[:-1]:
        obj = getattr(obj, part)
    return obj, field

def traverse_getattr(obj, fieldspec):
    obj, field = traverse_object(obj, fieldspec)
    return getattr(obj, field)

@register.assignment_tag(takes_context=True)
def more_paginator(context, objects, per_page=10, ordered_by='id'):
    request = context['request']
    if ordered_by[0] == '-':
        field = ordered_by[1:]
        op = 'lt'
    else:
        field = ordered_by
        op = 'gt'
    get_param = 'pagemore_after'
    get_param_ts = 'pagemore_ts'
    after_val = request.GET.get(get_param)
    is_timestamp = request.GET.get(get_param_ts, False)
    if after_val is not None:
        if is_timestamp:
            try:
                after_val = datetime.fromtimestamp(float(after_val))
            except TypeError:
                pass
        objects = objects.filter(**{field + '__' + op: after_val} )
    objects = list(objects[0:per_page+1]) # evaluate qs, intentionally
    has_more = len(objects) > per_page
    objects = objects[0:per_page]
    object_count = len(objects) 
    if object_count:
        next_after_val = traverse_getattr(objects[-1], field)
        if isinstance(next_after_val, datetime):
            is_timestamp = True
            next_after_val = time.mktime(next_after_val.timetuple())
    else:
        next_after_val = None
    get = request.GET.copy()
    get[get_param] = next_after_val
    get[get_param_ts] = '1' if is_timestamp else ''
    return dict(objects=objects,
                object_count=object_count,
                has_more=has_more,
                next_query=get.urlencode(),
                next_after_val=next_after_val)

