from django import template
from django.templatetags.static import StaticNode

register = template.Library()


class FeaturesStaticNode(StaticNode):
    def url(self, context):
        return self.handle_simple(
            self.path.resolve(context).format(context.get('device_features'))
        )


@register.tag('static')
def do_static(parser, token):
    """
    Static loader based on features; all feature parameters are formatted in,
    so you can use {screen} or {input_device} in your paths.
    """
    return FeaturesStaticNode.handle_token(parser, token)
