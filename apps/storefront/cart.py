"""
Cart helper — stores cart data in the Django session.

Session structure:
    request.session['cart'] = {
        '<product_id>': {
            'product_id': int,
            'variant_id': int|None,
            'title':      str,
            'slug':       str,
            'price':      str (Decimal as string),
            'image':      str|None,
            'emoji':      str,
            'qty':        int,
        },
        ...
    }

Keys are '<product_id>' or '<product_id>_<variant_id>' when a variant is selected.
"""

from decimal import Decimal
from django.conf import settings


CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    # ── Internal ──────────────────────────────────────────────────────────────

    def _save(self):
        self.session.modified = True

    def _key(self, product_id, variant_id=None):
        if variant_id:
            return f'{product_id}_{variant_id}'
        return str(product_id)

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, product, qty=1, variant=None, override_qty=False):
        """Add or update an item in the cart."""
        key = self._key(product.pk, variant.pk if variant else None)

        # Build image URL safely
        image_url = None
        feat = product.images.filter(is_feature=True).first() or product.images.first()
        if feat:
            image_url = feat.image.url

        if key not in self.cart:
            self.cart[key] = {
                'product_id': product.pk,
                'variant_id': variant.pk if variant else None,
                'title':      product.title,
                'slug':       product.slug,
                'price':      str(variant.final_price if variant else product.price),
                'image':      image_url,
                'emoji':      product.category.emoji if product.category else '🧸',
                'qty':        0,
            }

        if override_qty:
            self.cart[key]['qty'] = int(qty)
        else:
            self.cart[key]['qty'] += int(qty)

        # Clamp to stock
        max_stock = variant.stock if variant else product.stock
        self.cart[key]['qty'] = min(self.cart[key]['qty'], max_stock) if max_stock > 0 else self.cart[key]['qty']

        if self.cart[key]['qty'] <= 0:
            del self.cart[key]

        self._save()

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self._save()

    def update_qty(self, key, qty):
        if key in self.cart:
            qty = int(qty)
            if qty <= 0:
                self.remove(key)
            else:
                self.cart[key]['qty'] = qty
                self._save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.cart = self.session[CART_SESSION_KEY]
        self._save()

    # ── Computed Properties ───────────────────────────────────────────────────

    def __iter__(self):
        for key, item in self.cart.items():
            item['key']        = key
            item['line_total'] = Decimal(item['price']) * item['qty']
            yield item

    def __len__(self):
        return sum(item['qty'] for item in self.cart.values())

    @property
    def total(self):
        return sum(Decimal(item['price']) * item['qty'] for item in self.cart.values())

    @property
    def delivery_fee(self):
        if self.item_count == 0 or self.total >= Decimal('1000'):
            return Decimal('0.00')
        return Decimal('60.00')

    @property
    def grand_total(self):
        return self.total + self.delivery_fee

    @property
    def item_count(self):
        return len(self)

    def as_dict(self):
        """Serializable summary for AJAX responses."""
        return {
            'item_count':   self.item_count,
            'count':        self.item_count,
            'total':        str(self.total),
            'delivery_fee': str(self.delivery_fee),
            'grand_total':  str(self.grand_total),
            'items': [
                {
                    'key':        k,
                    'product_id': v['product_id'],
                    'title':      v['title'],
                    'price':      v['price'],
                    'qty':        v['qty'],
                    'image':      v['image'],
                    'emoji':      v['emoji'],
                    'line_total': str(Decimal(v['price']) * v['qty']),
                }
                for k, v in self.cart.items()
            ],
        }
