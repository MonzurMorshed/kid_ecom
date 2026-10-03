from django.db import models
from django.conf import settings
from products.models import Product, ProductVariant


# =========================================================
# CartItem  —  DB-backed cart row
# =========================================================
#
# Dual-key design:
#   • Guest carts:    session_key is set, user is NULL.
#   • Auth carts:     user is set, session_key may also be set.
#
# The Cart helper class in cart.py is the only thing that
# reads/writes these rows; templates never touch the model
# directly.
# =========================================================

class CartItem(models.Model):
    """
    Persistent cart line. Kept in sync with the session cart
    by the Cart helper so that the existing session-based flow
    continues to work for guests, while authenticated customers
    get a durable cart that survives browser restarts.
    """

    # ── Identity ──────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart_items',
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
        help_text='Django session key — used for anonymous carts.',
    )

    # ── Product ───────────────────────────────────────────
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='in_carts',
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='in_carts',
    )

    quantity = models.PositiveIntegerField(default=1)

    # Snapshot the price at the time the item was added so
    # that price changes don't silently alter existing carts.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        # Each (user, product, variant) or (session, product, variant) combo
        # should have at most one row — quantity accumulates on that row.
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product', 'variant'],
                condition=models.Q(user__isnull=False),
                name='unique_user_cart_item',
            ),
            models.UniqueConstraint(
                fields=['session_key', 'product', 'variant'],
                condition=models.Q(session_key__isnull=False, user__isnull=True),
                name='unique_session_cart_item',
            ),
        ]
        ordering = ['created_at']

    def __str__(self):
        who = self.user or self.session_key or '?'
        return f'CartItem({who}) — {self.quantity}× {self.product.title}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity
