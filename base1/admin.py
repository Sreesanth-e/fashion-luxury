# your_app/admin.py
from django.contrib import admin
from .models import Product, Cart, CartItem, Order, Subscription

# Register Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'category', 'is_new', 'created_at')
    list_filter = ('category', 'is_new')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

# Register Cart
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'created_at')
    list_filter = ('user',)
    search_fields = ('user__username', 'session_id')

# Register CartItem
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'get_total_price')
    list_filter = ('cart', 'product')
    search_fields = ('product__name',)

# Register Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'user', 'status', 'total_price', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'cart__id', 'session_id')
    list_editable = ('status',)  # Allows editing status directly in the list view

    # Optional: Add a custom method to display cart items in the detail view
    def get_cart_items(self, obj):
        return ", ".join([f"{item.quantity} x {item.product.name}" for item in obj.cart.items.all()])
    get_cart_items.short_description = "Cart Items"

    # Optional: Customize the detail view
    fieldsets = (
        (None, {
            'fields': ('cart', 'user', 'session_id', 'status', 'total_price', 'payment_method', 'created_at')
        }),
    )
    readonly_fields = ('created_at',)  # Make created_at read-only

# Register Subscription
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    list_filter = ('subscribed_at',)
    search_fields = ('email',)
    date_hierarchy = 'subscribed_at'  # Optional: Adds a date-based navigation