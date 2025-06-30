# your_app/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Product, Cart, CartItem, Order, Subscription

def home(request):
    cart = get_cart(request)
    cart_items = cart.items.all()
    cart_count = sum(item.quantity for item in cart_items)
    
    if request.method == 'POST' and 'subscribe' in request.POST:
        email = request.POST.get('email')
        if email:
            # Check if email already exists
            if Subscription.objects.filter(email=email).exists():
                messages.warning(request, 'This email is already subscribed.')
            else:
                Subscription.objects.create(email=email)
                messages.success(request, 'Thank you for subscribing!')
        else:
            messages.error(request, 'Please enter a valid email.')
        return redirect('home')
    
    return render(request, 'home.html', {'cart_count': cart_count})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        except User.DoesNotExist:
            pass
        messages.error(request, 'Invalid email or password.')
    return render(request, 'home.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('signup')
        
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        login(request, user)
        return redirect('home')
    
    return render(request, 'home.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

def product_list(request):
    products = Product.objects.filter(is_new=False)
    categories = Product.CATEGORY_CHOICES
    cart = get_cart(request)
    cart_items = cart.items.all()
    cart_count = sum(item.quantity for item in cart_items)
    context = {
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
    }
    return render(request, 'products.html', context)

def category_detail(request, category):
    products = Product.objects.filter(category=category)
    category_name = dict(Product.CATEGORY_CHOICES).get(category, category.capitalize())
    return render(request, 'category_details.html', {'products': products, 'category_name': category_name})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    cart = get_cart(request)
    cart_items = cart.items.all()
    cart_count = sum(item.quantity for item in cart_items)
    context = {
        'product': product,
        'cart_count': cart_count,
    }
    return render(request, 'product_details.html', context)

def get_cart(request):
    if request.user.is_authenticated:
        carts = Cart.objects.filter(user=request.user)
        if carts.count() > 1:
            latest_cart = carts.order_by('-id').first()
            carts.exclude(id=latest_cart.id).delete()
            cart = latest_cart
        else:
            cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.get('cart_session_id')
        if not session_id:
            if not request.session.session_key:
                request.session.create()
            session_id = request.session.session_key
            request.session['cart_session_id'] = session_id
        carts = Cart.objects.filter(session_id=session_id)
        if carts.count() > 1:
            latest_cart = carts.order_by('-id').first()
            carts.exclude(id=latest_cart.id).delete()
            cart = latest_cart
        else:
            cart, created = Cart.objects.get_or_create(session_id=session_id)
    return cart

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({'success': True, 'message': 'Added successfully to cart'})
    return redirect('cart_view')

def cart_view(request):
    cart = get_cart(request)
    cart_items = cart.items.all()
    total_price = sum(item.get_total_price() for item in cart_items)
    cart_count = sum(item.quantity for item in cart_items)
    latest_order = Order.objects.filter(cart=cart).order_by('-created_at').first()
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': cart_count,
        'latest_order': latest_order,
    }
    return render(request, 'cart.html', context)

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({'success': True, 'message': 'Item removed from cart'})
    return redirect('cart_view')

def checkout(request):
    if request.method == 'POST':
        cart = get_cart(request)
        cart_items = cart.items.all()
        if not cart_items:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart_view')
        
        total_price = sum(item.get_total_price() for item in cart_items)
        payment_method = request.POST.get('payment_method', 'cash')
        
        order = Order.objects.create(
            cart=cart,
            user=request.user if request.user.is_authenticated else None,
            session_id=cart.session_id if not request.user.is_authenticated else None,
            total_price=total_price,
            payment_method=payment_method,
            status='Pending'
        )
        
        cart_items.delete()
        messages.success(request, f'Your order (#{order.id}) has been successfully placed!')
        return redirect('cart_view')
    return redirect('cart_view')