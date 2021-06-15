from django import template
register = template.Library()


def sizeformat(value):
    if value == None:
        return None
    if value < 1000:
        if value < 2:
            return str(value) + " byte"
        else:
            return str(value) + " bytes"
    elif value < 1000000:
        value = round(float(value/1000), 3)
        return str(value) + " KB"
    elif value < 1000000000:
        value = round(float(value / 1000000), 3)
        return str(value) + " MB"
    elif value < 1000000000000:
        value = round(float(value / 1000000000), 3)
        return str(value) + " GB"
    else:
        value = round(float(value / 1000000000000), 3)
        return str(value) + " TB"

register.filter('sizeformat', sizeformat)