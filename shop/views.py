from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Min
from .models import Product, CustomerProfile, Address, HomePageFeatured


# ====================== BASIC VIEWS ======================

def home(request):
    # Fetch only one "Featured" entry (you can extend later if you want multiple sections)
    featured = HomePageFeatured.objects.first()

    products = []
    if featured:
        products = featured.products.all()[:featured.max_items]

    return render(request, 'shop/index.html', {
        'products': products,
        'featured_title': featured.title if featured else "Featured Products"
    })



from .models import Product, ProductVariant  # make sure ProductVariant is imported

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # Fetch all variants of the product
    variants = product.variants.all().order_by('price')  # lowest price first

    # Pick the cheapest variant as default
    default_variant = variants.first() if variants else None

    # Related products
    related_products = Product.objects.exclude(id=product.id).annotate(
    lowest_price=Min('variants__price'))[:8]

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'variants': variants,
        'default_variant': default_variant,
        'related_products': related_products,
    })

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirmation = request.POST.get('password_confirmation')

        if password != password_confirmation:
            messages.error(request, "Passwords do not match.")
            return render(request, 'shop/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'shop/register.html')

        # split name into first and last names
        first_name = name.split(' ')[0]
        last_name = ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''

        # use email as username
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # add to Customer group if it exists
        try:
            customer_group = Group.objects.get(name='Customer')
            user.groups.add(customer_group)
        except Group.DoesNotExist:
            pass

        # log the user in
        backend = get_backends()[0]
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(request, user)

        return redirect('home')

    return render(request, 'shop/register.html')


class CustomLoginView(LoginView):
    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


def logout_view(request):
    logout(request)
    return redirect('home')



# ====================== PROFILE VIEWS ======================

@login_required
def profile_view(request):
    user = request.user
    profile, _ = CustomerProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.save()

        profile.phone = request.POST.get("phone", "")
        profile.city = request.POST.get("city", "")
        profile.state = request.POST.get("state", "")
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    addresses = user.addresses.all()
    return render(request, "shop/profile.html", {
        "profile": profile,
        "addresses": addresses,
        "user": user
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
        profile.city = request.POST.get("city", "")
        profile.state = request.POST.get("state", "")
        profile.save()

        messages.success(request, "Profile updated successfully.")
    return redirect("profile")



# ====================== ADDRESS CRUD ======================

@login_required
def save_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == "POST":
        address.flat = request.POST.get("flat", "")
        address.area = request.POST.get("area", "")
        address.landmark = request.POST.get("landmark", "")
        address.pincode = request.POST.get("pincode", "")
        address.city = request.POST.get("city", "")
        address.state = request.POST.get("state", "")
        address.contact = request.POST.get("contact", "")

        selected = request.POST.get("selected")
        if selected and int(selected) == address.id:
            # Mark all others unselected
            Address.objects.filter(user=request.user).update(is_selected=False)
            address.is_selected = True

        address.save()
    return redirect("profile")

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
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
            contact=request.POST.get("contact", "")
        )
        return redirect("profile")

    return render(request, "shop/add_address.html")  # create this template with a simple form



from .models import Product, ProductVariant
from django.urls import reverse

def add_to_cart(request):
    if request.method == 'POST':
        product_slug = request.POST.get('product_slug')
        variant_weight = request.POST.get('variant_weight')
        quantity = int(request.POST.get('quantity', 1))

        try:
            product = Product.objects.get(slug=product_slug)
            variant = product.variants.get(weight=variant_weight)

            if request.user.is_authenticated:
                # ✅ Save to DB
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user,
                    variant=variant,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
            else:
                # ✅ Save to session (for guest users)
                cart = request.session.get('cart', {})
                if product_slug in cart and variant_weight in cart[product_slug]:
                    cart[product_slug][variant_weight]['quantity'] += quantity
                else:
                    cart.setdefault(product_slug, {})[variant_weight] = {
                        'quantity': quantity
                    }
                request.session['cart'] = cart

            messages.success(request, "Added to cart!")  
            return redirect(reverse('product_detail', args=[product.slug]))

        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            return redirect('home')

    return redirect('home')


def cart_view(request):
    cart_items = []
    grand_total = 0

    if request.user.is_authenticated:
        # ✅ Fetch from DB
        db_cart_items = CartItem.objects.filter(user=request.user).select_related('variant__product')
        for item in db_cart_items:
            total_price = item.variant.price * item.quantity
            cart_items.append({
                'product': item.variant.product,
                'variant': item.variant,
                'quantity': item.quantity,
                'total_price': total_price
            })
            grand_total += total_price
    else:
        # ✅ Load from session
        session_cart = request.session.get('cart', {})
        for product_slug, variants in session_cart.items():
            try:
                product = Product.objects.get(slug=product_slug)
                for weight, info in variants.items():
                    variant = product.variants.get(weight=weight)
                    quantity = info['quantity']
                    total_price = variant.price * quantity

                    cart_items.append({
                        'product': product,
                        'variant': variant,
                        'quantity': quantity,
                        'total_price': total_price
                    })
                    grand_total += total_price
            except Product.DoesNotExist:
                continue

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })


from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from .models import CartItem, Product, ProductVariant

@require_POST
def remove_from_cart(request):
    product_slug = request.POST.get('product_slug')
    variant_weight = request.POST.get('variant_weight')

    try:
        product = Product.objects.get(slug=product_slug)
        variant = ProductVariant.objects.get(product=product, weight=variant_weight)

        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(user=request.user, variant=variant)
            cart_item.delete()
        else:
            cart = request.session.get('cart', {})
            if variant.slug in cart:
                del cart[variant.slug]
                request.session['cart'] = cart

    except (Product.DoesNotExist, ProductVariant.DoesNotExist, CartItem.DoesNotExist):
        pass

    return redirect('cart')

from django.http import JsonResponse

@require_POST
def update_cart_quantity(request):
    product_slug = request.POST.get('product_slug')
    variant_weight = request.POST.get('variant_weight')
    quantity = int(request.POST.get('quantity', 1))

    try:
        product = Product.objects.get(slug=product_slug)
        variant = product.variants.get(weight=variant_weight)

        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(user=request.user, variant=variant)
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart = request.session.get('cart', {})
            if product_slug in cart and variant_weight in cart[product_slug]:
                cart[product_slug][variant_weight]['quantity'] = quantity
                request.session['cart'] = cart

        return JsonResponse({'success': True})

    except (Product.DoesNotExist, ProductVariant.DoesNotExist, CartItem.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Item not found'})


from .models import Category  # add at the top if not already

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'shop/category_list.html', {'categories': categories})

def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).annotate(
        lowest_price=Min('variants__price')
    )
    return render(request, 'shop/category_detail.html', {
        'category': category,
        'products': products,
    })


from .models import Product

def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).prefetch_related('variants')

    # Attach cheapest variant to each product
    for product in products:
        cheapest_variant = product.variants.order_by('price').first()
        product.cheapest_variant = cheapest_variant  # dynamically attach it

    return render(request, 'shop/category_detail.html', {
        'category': category,
        'products': products
    })

@login_required
def final_checkout(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('variant__product')
    addresses = Address.objects.filter(user=user)

    subtotal = 0
    for item in cart_items:
        subtotal += item.variant.price * item.quantity

    delivery_fee = 50 if subtotal < 500 else 0  # example rule
    total = subtotal + delivery_fee

    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'addresses': addresses,
    })

from django.shortcuts import redirect

@login_required
def add_address_checkout(request):
    if request.method == 'POST':
        user = request.user
        flat = request.POST.get('flat') 
        landmark = request.POST.get('landmark')
        area = request.POST.get('area')
        city = request.POST.get('city')
        state = request.POST.get('state')
        contact = request.POST.get('contact')
        pincode = request.POST.get('pincode')
        use_for_order = request.POST.get('use_for_order') == 'on'

        if use_for_order:
            # Unselect all other addresses
            Address.objects.filter(user=user).update(is_selected=False)

        Address.objects.create(
            user=user,
            flat=flat,
            landmark=landmark,
            area=area,
            city=city,
            state=state,
            contact=contact,
            pincode=pincode,
            is_selected=use_for_order
        )

        return redirect('checkout')  # Replace 'checkout' with the name of your checkout view
    

@login_required
def validate_address(request, id):
    exists = Address.objects.filter(id=id, user=request.user).exists()
    return JsonResponse({'exists': exists})

from .models import Order, OrderItem, CartItem, Address
from django.views.decorators.csrf import csrf_exempt


@login_required
@csrf_exempt  # since you may POST from popup
def order_confirmation(request):
    if request.method == "POST":
        payment_status = request.POST.get("payment_status")  # "success" / "failed"
        address_id = request.POST.get("address_id")

        # ✅ Get selected address
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            return redirect("checkout")

        # ✅ Collect cart
        cart_items = CartItem.objects.filter(user=request.user).select_related('variant__product')

        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect("cart")

        # ✅ Calculate totals
        subtotal = sum([item.variant.price * item.quantity for item in cart_items])
        delivery_fee = 50 if subtotal < 500 else 0
        total = subtotal + delivery_fee

        # ✅ Create Order
        order = Order.objects.create(
            user=request.user,
            address=address,
            total_price=total,
            payment_status="Completed" if payment_status == "success" else "Failed",
            status="Pending" if payment_status == "success" else "Cancelled"
        )

        # ✅ Add OrderItems
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                price=item.variant.price
            )

        # ✅ Clear cart
        cart_items.delete()

        return render(request, "shop/confirmation.html", {
            "order": order,
            "payment_status": payment_status,
        })

    return redirect("checkout")


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "shop/my_orders.html", {"orders": orders})

@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "shop/order_details.html", {"order": order})
