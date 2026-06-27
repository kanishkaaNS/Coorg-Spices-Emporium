from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    weight = models.CharField(max_length=50)  # e.g., "100g", "250g", "1kg"
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.weight}"

    class Meta:
        unique_together = ('product', 'weight')

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_gallery/')
    alt_text = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.alt_text or f"Extra image for {self.product.name}"

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    flat = models.CharField(max_length=255)
    area = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255)
    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    is_selected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.flat}, {self.city}"


from django.views.decorators.csrf import csrf_exempt
from .models import CustomerProfile, Address
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def profile_view(request):
    user = request.user
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    addresses = Address.objects.filter(user=user)
    return render(request, "shop/profile.html", {
        "profile": profile,
        "addresses": addresses,
    })

@login_required
def save_profile(request):
    if request.method == "POST":
        user = request.user
        profile, _ = CustomerProfile.objects.get_or_create(user=user)

        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.save()

        profile.phone = request.POST.get("phone", "")
        profile.save()

        return redirect("profile")
    return redirect("profile")

@login_required
def save_address(request, address_id):
    address = Address.objects.get(id=address_id, user=request.user)

    if request.method == "POST":
        address.flat = request.POST.get("flat", "")
        address.area = request.POST.get("area", "")
        address.landmark = request.POST.get("landmark", "")
        address.pincode = request.POST.get("pincode", "")
        address.city = request.POST.get("city", "")
        address.state = request.POST.get("state", "")
        address.contact = request.POST.get("contact", "")
        address.save()

        # Unselect all other addresses
        Address.objects.filter(user=request.user).exclude(id=address.id).update(is_selected=False)

        # Check if this is selected
        if request.POST.get("selected") == str(address.id):
            address.is_selected = True
            address.save()

    return redirect("profile")

@login_required
def delete_address(request, address_id):
    Address.objects.filter(id=address_id, user=request.user).delete()
    return redirect("profile")

@login_required
def add_address(request):
    if request.method == "POST":
        Address.objects.create(
            user=request.user,
            flat=request.POST.get("flat", ""),
            area=request.POST.get("area", ""),
            landmark=request.POST.get("landmark", ""),
            pincode=request.POST.get("pincode", ""),
            city=request.POST.get("city", ""),
            state=request.POST.get("state", ""),
            contact=request.POST.get("contact", ""),
            is_selected=True
        )
        return redirect("profile")

    return render(request, "shop/add_address.html")

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.variant.product.name} ({self.variant.weight}) x {self.quantity}"

    def total_price(self):
        return self.variant.price * self.quantity

@login_required
def checkout(request):
    user = request.user

    if request.method == 'POST':
        # Get form data
        flat = request.POST.get('flat')
        area = request.POST.get('area')
        landmark = request.POST.get('landmark')
        pincode = request.POST.get('pincode')
        city = request.POST.get('city')
        state = request.POST.get('state')
        contact = request.POST.get('contact')
        is_selected = request.POST.get('is_selected') == 'on'

        if is_selected:
            # Unselect previously selected addresses
            Address.objects.filter(user=user).update(is_selected=False)

        # Save new address
        Address.objects.create(
            user=user,
            flat=flat,
            area=area,
            landmark=landmark,
            pincode=pincode,
            city=city,
            state=state,
            contact=contact,
            is_selected=is_selected
        )

        return redirect('checkout')  # Refresh to show the new address

    # GET request: show checkout page with saved addresses
    addresses = Address.objects.filter(user=user)
    context = {'addresses': addresses}
    return render(request, 'checkout.html', context)

import uuid
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    order_number = models.CharField(max_length=8, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.order_number:
            # generate a unique 8-digit number
            while True:
                num = str(uuid.uuid4().int)[:8]
                if not Order.objects.filter(order_number=num).exists():
                    self.order_number = num
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # store price at order time

    def __str__(self):
        return f"{self.variant.product.name} - {self.variant.weight} (x{self.quantity})"

class HomePageFeatured(models.Model):
    title = models.CharField(max_length=100, default="Featured Products")
    products = models.ManyToManyField(Product, help_text="Select products to display on the homepage")
    max_items = models.PositiveIntegerField(default=12, help_text="Limit number of products displayed")

    def __str__(self):
        return self.title
