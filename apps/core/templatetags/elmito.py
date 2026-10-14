from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _indian_group(integer: str) -> str:
    if len(integer) <= 3:
        return integer
    head, tail = integer[:-3], integer[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


@register.filter
def inr(value):
    """₹1,49,999 style formatting; decimals only when needed."""
    try:
        amount = Decimal(value).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return ""
    whole, _, fraction = f"{amount:.2f}".partition(".")
    text = _indian_group(whole)
    return f"₹{text}" if fraction == "00" else f"₹{text}.{fraction}"


@register.filter
def savings_percent(product):
    if not product.discount_price:
        return 0
    return int(round((1 - product.discount_price / product.price) * 100))
