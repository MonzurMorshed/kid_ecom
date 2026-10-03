"""
Cart helper — hybrid session + DB cart.

For **guest** users the cart lives entirely in the Django session
(same dict schema as before — zero breaking changes to templates).

For **authenticated customers** the session is kept as a fast
read-through cache but every mutation is also written to the
``CartItem`` DB model in ``storefront.models``.  This gives customers
a durable cart that survives browser restarts, device switches, and
session expiry.

On **login** any existing guest-session items are merged into the
user's DB cart and the session is rebuilt from the merged DB rows.

Session structure (unchanged):
    request.session['cart'] = {
        '<key>': {
            'product_id': int,
            'variant_id': int|None,
            'title':      str,
            'slug':       str,
            'price':      str  (Decimal as string),
            'image':      str|None,
            'emoji':      str,
            'qty':        int,
        },
        ...
    }

Keys: '<product_id>' or '<product_id>_<variant_id>'
"""

from decimal import Decimal
from django.conf import settings


CART_SESSION_KEY = 'cart'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _item_key(product_id, variant_id=None):
    if variant_id:
        return f'{product_id}_{variant_id}'
    return str(product_id)


def _build_item_dict(product, variant=None, qty=0):
    """Build the session-dict representation of a cart line."""
    image_url = None
    feat = product.images.filter(is_feature=True).first() or product.images.first()
    if feat:
        image_url = feat.image.url

    price = variant.final_price if variant else product.price
    return {
        'product_id': product.pk,
        'variant_id': variant.pk if variant else None,
        'title':      product.title,
        'slug':       product.slug,
        'price':      str(price),
        'image':      image_url,
        'emoji':      product.category.emoji if product.category else '🧸',
        'qty':        qty,
    }


# ── Main Cart class ───────────────────────────────────────────────────────────

class Cart:
    """
    Hybrid cart.

    Usage is identical to the old session-only Cart — templates and
    views do not need to change.  The DB layer is completely
    transparent.
    """

    def __init__(self, request):
        self.session  = request.session
        self.request  = request
        self._user    = request.user if request.user.is_authenticated and not request.user.is_staff else None

        # Always load from session first (cheap, no DB hit)
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = {}

        # Authenticated customers: rebuild session from DB so it's
        # always the authoritative source.
        if self._user:
            cart = self._load_from_db()

        self.session[CART_SESSION_KEY] = cart
        self.cart = self.session[CART_SESSION_KEY]

    # ── Private: DB layer ─────────────────────────────────────────────────────

    def _load_from_db(self):
        """
        Fetch all CartItem rows for the current user and return a
        session-compatible dict.  Creates the session dict from scratch
        so the session always reflects the DB.
        """
        from .models import CartItem
        items = (
            CartItem.objects
            .filter(user=self._user)
            .select_related('product__category', 'variant')
            .prefetch_related('product__images')
        )
        cart = {}
        for ci in items:
            key = _item_key(ci.product_id, ci.variant_id)
            d   = _build_item_dict(ci.product, ci.variant, qty=ci.quantity)
            d['price'] = str(ci.unit_price)   # use stored price snapshot
            cart[key]  = d
        return cart

    def _db_upsert(self, product, variant, qty, unit_price):
        """Create or update a CartItem row for an authenticated user."""
        if not self._user:
            return
        from .models import CartItem
        CartItem.objects.update_or_create(
            user=self._user,
            product=product,
            variant=variant,
            defaults={'quantity': qty, 'unit_price': unit_price},
        )

    def _db_delete(self, product_id, variant_id):
        """Delete a CartItem row for an authenticated user."""
        if not self._user:
            return
        from .models import CartItem
        CartItem.objects.filter(
            user=self._user,
            product_id=product_id,
            variant_id=variant_id,
        ).delete()

    def _db_clear(self):
        """Delete all CartItem rows for an authenticated user."""
        if not self._user:
            return
        from .models import CartItem
        CartItem.objects.filter(user=self._user).delete()

    def _save(self):
        self.session.modified = True

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, product, qty=1, variant=None, override_qty=False):
        """Add or update a line item."""
        key       = _item_key(product.pk, variant.pk if variant else None)
        price     = variant.final_price if variant else product.price
        max_stock = (variant.stock if variant else product.stock) or 0

        if key not in self.cart:
            self.cart[key] = _build_item_dict(product, variant, qty=0)

        if override_qty:
            self.cart[key]['qty'] = int(qty)
        else:
            self.cart[key]['qty'] += int(qty)

        # Clamp to stock
        if max_stock > 0:
            self.cart[key]['qty'] = min(self.cart[key]['qty'], max_stock)

        new_qty = self.cart[key]['qty']
        if new_qty <= 0:
            del self.cart[key]
            self._db_delete(product.pk, variant.pk if variant else None)
        else:
            # Keep price snapshot up-to-date on every add
            self.cart[key]['price'] = str(price)
            self._db_upsert(product, variant, new_qty, price)

        self._save()

    def remove(self, key):
        if key in self.cart:
            item = self.cart[key]
            self._db_delete(item['product_id'], item.get('variant_id'))
            del self.cart[key]
            self._save()

    def update_qty(self, key, qty):
        if key in self.cart:
            qty = int(qty)
            if qty <= 0:
                self.remove(key)
            else:
                self.cart[key]['qty'] = qty
                item = self.cart[key]
                # Update DB
                if self._user:
                    from .models import CartItem
                    CartItem.objects.filter(
                        user=self._user,
                        product_id=item['product_id'],
                        variant_id=item.get('variant_id'),
                    ).update(quantity=qty)
                self._save()

    def clear(self):
        self._db_clear()
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
        """Serialisable summary for AJAX responses."""
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


# ── Login merge helper ────────────────────────────────────────────────────────

def merge_session_cart_to_user(request, user):
    """
    Call this right after a successful login to move any anonymous
    session-cart items into the user's DB cart and rebuild the session.

    Usage in login view::

        from apps.storefront.cart import merge_session_cart_to_user
        login(request, user)
        merge_session_cart_to_user(request, user)
    """
    if user.is_staff or user.is_superuser:
        return

    from products.models import Product, ProductVariant
    from .models import CartItem

    session_cart = request.session.get(CART_SESSION_KEY, {})

    for key, item in session_cart.items():
        try:
            product = Product.objects.get(pk=item['product_id'], is_active=True, is_deleted=False)
            variant = None
            if item.get('variant_id'):
                variant = ProductVariant.objects.filter(pk=item['variant_id']).first()

            price = Decimal(item['price'])
            qty   = int(item['qty'])

            ci, created = CartItem.objects.get_or_create(
                user=user,
                product=product,
                variant=variant,
                defaults={'quantity': qty, 'unit_price': price},
            )
            if not created:
                # Merge: add quantities (clamped to stock later by Cart.add)
                ci.quantity += qty
                ci.unit_price = price
                ci.save(update_fields=['quantity', 'unit_price', 'updated_at'])
        except Exception:
            continue   # Skip malformed or deleted products

    # Rebuild session from the merged DB state
    cart = Cart.__new__(Cart)
    cart._user   = user
    cart.session = request.session
    request.session[CART_SESSION_KEY] = cart._load_from_db()
    request.session.modified = True
