from django.contrib import admin

from .models import Category, EmailTemplate, SubCategory, User ,Module, ShopProduct, ShopProductImage,SheroDollsImageSubTable,ProductOrder,ProductOrderData,UserAddress, Country,ProductCollection,WebCountry , WebState,Offer,WebCity,GuestUserData


# from adminpanel.models import Contact

# Register your models here.
# model = CustomAuthUser
# list_display = ['username', 'password', 'email', 'mobile_number',]
# class MyUserAdmin:
#     add_form = CustomUserCreationForm
#     form = CustomUserChangeForm
#     model = CustomUser
#     list_display = ["email", "username", "mobile_number"]
# fieldsets = UserAdmin.fieldsets + (
#     (None, {'fields': ('mobile_number', 'birth_date')}),
# )  # this will allow to change these fields in admin module


admin.site.register([EmailTemplate, Category, SubCategory, User,Module,ShopProduct,ShopProductImage,SheroDollsImageSubTable,ProductOrder,ProductOrderData,UserAddress,ProductCollection,Country,WebCountry , WebState,Offer,WebCity,GuestUserData])

