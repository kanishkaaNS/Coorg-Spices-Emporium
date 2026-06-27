from django import template

register = template.Library()

@register.filter
def get_main_image(images):
    main = images.filter(alt_text='Main_Image').first()
    return main.image.url if main else ''

@register.filter
def get_side_image(images, label):
    side = images.filter(alt_text=label).first()
    return side.image.url if side else ''
