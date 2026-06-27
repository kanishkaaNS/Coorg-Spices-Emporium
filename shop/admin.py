from django.contrib import admin
from .models import (
    Product, Category, ProductImage, ProductVariant,
    CustomerProfile, Address, Order, OrderItem, HomePageFeatured
)

# ================= Product Inlines =================

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # empty slots for variants

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # empty slots for additional images
    fields = ('image', 'alt_text')

# ================= Product Admin =================

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]

# ================= Category Admin =================

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    fields = ('name', 'image')  # so you can upload image directly in admin

# ================= Order Admin =================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "payment_status", "total_price", "created_at")
    list_filter = ("status", "payment_status", "created_at")
    search_fields = ("order_number", "user__username", "user__email")
    inlines = [OrderItemInline]

# ================= HomePage Featured =================

class HomePageFeaturedAdmin(admin.ModelAdmin):
    filter_horizontal = ('products',)
    list_display = ('title', 'max_items')

# ================= Register Models =================

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(CustomerProfile)
admin.site.register(Address)
admin.site.register(Order, OrderAdmin)
admin.site.register(HomePageFeatured, HomePageFeaturedAdmin)
