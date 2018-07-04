from django import template

register = template.Library()

@register.filter(name='get')
def get(d, k):
    return d.get(k, None)

@register.filter(name='entity')
def entity(d, k):
    v = d.get(k, None) if d else None
    return v[0].get('value') if v and len(v) else None

@register.filter(name='duration')
def duration(seconds):
    if not seconds:
      return ''
    return '{} ms'.format(int(seconds * 1000))

