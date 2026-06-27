from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView
from .views import profile_view

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(template_name='shop/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('profile/', profile_view, name='profile'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    path('checkout/', views.final_checkout, name='checkout'),
    path('validate-address/<int:id>/', views.validate_address, name='validate-address'),
    path('add-address-checkout/', views.add_address_checkout, name='add_address_checkout'),
    path('confirmation/', views.order_confirmation, name='order_confirmation'),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("order-details/<int:order_id>/", views.order_details, name="order_details"),
]

from .views import (
    profile_view,
    save_profile,
    save_address,
    delete_address,
    add_address
)

urlpatterns += [
    path("profile/save/", save_profile, name="save_profile"),
    path("address/add/", add_address, name="add_address"),
    path("address/save/<int:address_id>/", save_address, name="save_address"),
    path("address/delete/<int:address_id>/", delete_address, name="delete_address"),
]

from django.contrib.auth import views as auth_views

urlpatterns += [
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'), name='password_reset_complete'),
]
