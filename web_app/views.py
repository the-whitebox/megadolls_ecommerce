from .helpers import generate_anonymous_id, string_to_list
from .encryption_util import text_decryption
from adminpanel.global_dict import interval_dict, STRIPE_TAX_CODE
from .custom_jwt_token import *
from sloper.time_function import get_unix_timestamp_of_one_month_later
from adminpanel.models import *
from web_app.models import *
from .serializers import *
from .email import *
from .ship_station import *
from .twilio import *
from .payment import *

from decimal import Decimal
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from collections import Counter
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from django.db.models import Avg, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
import requests, json, stripe, ast, random
from datetime import datetime, timedelta
from allauth.account.signals import user_signed_up, user_logged_in
from django.dispatch import receiver

NO_STOCK_MSG = "Required Quantity Not Available"

@receiver(user_signed_up)
def sign_up_customerID(request, **kwargs):
    user = kwargs['user']
    customer = create_customer(user.email)
    subscription_data = UserSubscriptions(user_id=user.id, customer_id=customer['id'])
    if SloperHospital.objects.filter(management_email = user.email).exists():
        role = "HOSPITAL"
    else:
        role = user.user_type    
    if not UserRole.objects.create(user_id = user.id).exists():
        UserRole.objects.create(user_id = user.id, role = role)
    subscription_data.save()


@receiver(user_logged_in)    
def sign_in_customerID(request, **kwargs):
    user = kwargs['user']
    if not UserSubscriptions.objects.filter(user_id=user.id).exists():
        customer = create_customer(user.email)
        subscription_data = UserSubscriptions(user_id=user.id, customer_id=customer['id'])
        subscription_data.save()

#Generate the random codes :
def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


def web_sign_up(request, slug=''):  
    if request.user.is_authenticated:
        return redirect('home')
    elif request.method == "POST":
        try:
            status = False
            name = request.POST.get('name')
            email = request.POST.get('email').lower()
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            referral_code = request.POST.get('referral')
            referral_link_code = request.POST.get("referral")
            user = None

            if not (name and not name.isspace()) or not (email and not email.isspace()) or not (password and not password.isspace()):
                raise ValueError("All Field Are Required")
            elif len(name) > 20:
                return JsonResponse({'status': status, 'message': 'Name length should be less than 20 character'}, safe=False)
            elif confirm_password == password:
                return JsonResponse({'status': status, 'message': 'Confirm Password Should Be Same as Password'}, safe=False)
            elif User.objects.filter(email=email, is_mail_send=True, is_verified=True).exists():
                return JsonResponse({'status': status, 'message': 'Account Aleady Exists'}, safe=False)
            if referral_code: 
                if not User.objects.filter(referral_code=referral_code).exists():
                    messages.error(request, "Wrong Referral Code")
                    return JsonResponse({'status': status, 'message': 'Wrong Referral Code', 'name': name, 'email': email})
                
            digits = random_with_N_digits(8)
            code_name = name.replace(" ", "").upper()
            new_referral_code = f"{code_name}{digits}"
            existed_user = User.objects.filter(email=email, is_verified=False)
            
            if existed_user.exists():
                user = existed_user.first()
                user.name = name
                user.password = make_password(str(password))
                user.referral_code = new_referral_code
                user.save()
            else:
                try:
                    user = User.objects.create(name=name, email=email, password=make_password(str(password)), user_type='CUSTOMER', referral_code=new_referral_code)
                except:
                    return JsonResponse({'status': False, 'message': 'Email Already Exists'}, safe=False)
                
                if referral_link_code:
                    referrer_user = User.objects.get(referral_code = referral_link_code)          
                    referrer_user_id = referrer_user.id
                    referred_user_id = user.id
                    UserReferral.objects.create(user_from_id = referrer_user_id, user_to_id = referred_user_id)

                # if referral_code:
                #     referrer_user = User.objects.get(referral_code = referral_code)          
                #     referrer_user_id = referrer_user.id
                #     referred_user_id = user.id
                #     UserReferral.objects.create(user_from_id = referrer_user_id, user_to_id = referred_user_id)
                Profile.objects.create(user_id = user.id)
                customer = create_customer(user.email)
                if not UserSubscriptions.objects.filter(user_id=user.id).exists():
                    subscription_data = UserSubscriptions(user_id=user.id, customer_id=customer['id'])
                    subscription_data.save()
                    
            verify_mail(user)
            user.is_mail_send = True
            user.save()

            if request.user.is_anonymous and request.session.has_key('anonymous_user'):
                a_id = request.session['anonymous_user']['a_id']
                cart = AnonymousCart.objects.get(a_id=a_id) 
                UserCart.objects.create(user_id=user.id, shop_product_list=cart.shop_product_list)
                cart.delete()

            status = True          

            return JsonResponse({'status': status}, safe=False)
        except ValueError as val_err:
            return JsonResponse({'status': False, 'message': 'All Fields Required'}, safe=False)
        except Exception as err:
            return JsonResponse({'status': False, 'message': 'Something Went Wrong', 'error': err}, safe=False)
    return render(request, 'web_sign_up.html', {"slug": slug})
    
def web_verify_mail(request, encrptyed_user_id):
    try:
        user_id = text_decryption(encrptyed_user_id)
        user_data = User.objects.get(id = user_id)
        name = user_data.name
        if User.objects.filter(id = user_id, is_verified=True):
            messages.success(request, "Already verified")
            return redirect('web_login')
        User.objects.filter(id = user_id).update(is_verified=True)
        messages.success(request, "Verification Successful")
    
        welcome_mail_for_signing_up(user_data.email, name)
        
        return redirect('web_login')
    except:
        messages.error(request, 'Something Went Wrong') 
        return redirect('web_sign_up')   


def web_forgot_password(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        email = request.POST.get('email').lower()
        if User.objects.filter(email=email).exists():
            if User.objects.filter(email=email, is_verified=False).exists():
                messages.error(request, "Please verify your account first")
                return redirect("web_forgot_password")
        
            userobj = User.objects.get(email=email)
            user_id = userobj.id
            if userobj:
                otp = random.randint(100000, 999999)
                userobj.otp = otp
                userobj.save()
                try:
                    mobile_number = userobj.mobile
                    msg = "Your OTP to reset password is, "
                    update_mobile(otp, msg, mobile_number)
                except:
                    pass 
                jwt_token = token(user_id)
                link = f'{settings.SITE_URL}otp/{jwt_token}'
                otp_to_reset_password(otp, email, link)
                messages.success(request, "OTP Sent to your Email")
                return redirect('/otp/' + jwt_token)
        else:
            messages.error(request, "User Does Not Exist")
            return render(request, 'forgot-password.html')
    return render(request, 'forgot-password.html')

def resend_otp(request, jwt_token):
    try:
        id = decode_token(jwt_token)
        user_data = User.objects.get(id=id['id'])
        email = user_data.email.lower()
        otp = random.randint(100000, 999999)
        user_data.otp = otp
        user_data.save()
        try:
            mobile_number = user_data.mobile
            msg = "Your OTP to reset password is, "
            update_mobile(otp, msg, mobile_number)
        except:
            pass    
        link = f'{settings.SITE_URL}otp/{jwt_token}'
        otp_to_reset_password(otp, email, link)
        messages.success(request, "OTP Sent to your Email")
        return redirect('/otp/' + jwt_token)
    except:
        messages.error(request, 'Something Went Wrong')
        return redirect('web_forgot_password')    
    

def otp(request, jwt_token):
    id = decode_token(jwt_token)
    mail = User.objects.get(id=id['id'])
    email = mail.email.lower()
    if request.method == "POST":
        otp = request.POST.get('otp')
        try:
            userobj = User.objects.get(email=email, is_delete=False)
        except:
            userobj = None  
        if userobj:
            if not otp:
                messages.error(request, 'Please Enter OTP')
                return redirect('/otp/' + jwt_token)
            if userobj.otp == otp:
                return redirect('/resetpassword/' + jwt_token)
            else:
                messages.error(request, 'Wrong OTP')               
            return redirect('/otp/' + jwt_token)
    return render(request, 'otp.html', {'email':email, 'jwt_token': jwt_token})


def resetpassword(request ,jwt_token):
    try:
        id = decode_token(jwt_token)
        user = User.objects.get(id=id['id'])     
        if request.method == "POST":
            password = request.POST.get('password')
            user.password = make_password(password)
            user.save()
            messages.success(request , 'Password has changes successfully')
            return redirect('web_login')
        return render(request, "reset-password.html")    
    except:
        messages.error(request, 'Something Went Wrong')
        return redirect('web_login')    
                

def web_login(request):
    # try:
        if request.user.is_authenticated:
            return redirect('home')
        elif request.method == "POST":
            email = request.POST.get('email').lower()
            password = request.POST.get('password')
            if not email:
                messages.error(request, "Please Enter Email")
                if request.POST.get('cart_redirect'):
                    return redirect('view_cart')
                return redirect('web_login')
            elif not password:
                messages.error(request, "Please Enter password")
                if request.POST.get('cart_redirect'):
                    return redirect('view_cart')
                return redirect('web_login')
            elif not User.objects.filter(email=email, is_delete=False):
                messages.error(request, "User Not Exists")
                if request.POST.get('cart_redirect'):
                    return redirect('view_cart')
                return redirect('web_login')
            elif email and password:
                user = User.objects.filter(email=email, is_delete=False)
                if user.filter(is_verified=True).exists():
                    verified_user = user.filter(is_verified=True).first()
                    if verified_user.check_password(password):
                        login(request, verified_user)
                        if request.POST.get('cart_redirect'):
                            messages.success(request, "Sign In Successfully")
                            return redirect('view_cart')
                        return redirect('home')
                    else:
                        messages.error(request, "Wrong Password")
                        return redirect('web_login')
                else:
                    non_verified_user = user.filter(is_verified=False).first()
                    verify_mail(non_verified_user)
                    non_verified_user.is_mail_send = True
                    non_verified_user.save()
                    messages.error(request, "Your Account is not Verified, Verification link sent to your Email ")
        return render(request, 'web_login.html')
    # except:
    #     messages.error(request, "Something Went Wrong")
    #     return render(request, 'web_login.html')


def web_logout(request):
    try:
        logout(request)
        return redirect("web_login")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('home')    


def home(request):
    #slider_data,product_shop_data,subscription_data,product_imagine_data used for the home page dynamic
    # get_order()
    user_id = request.user.id
    try:
        user_data = User.objects.get(id = user_id)
        if not user_data.name:
            first_name = user_data.first_name
            last_name = user_data.last_name
            name = f"{first_name} {last_name}"
            user_data.name = name
            user_data.save()
    except:
        pass
    slider_data=Slider.objects.all()
    product_shop_data=ProductShop.objects.all()
    what_is_new = ShopProduct.objects.filter(is_active = True, is_delete = False).order_by('-id')[:4]
    rating_avg = {}
    if request.user.is_authenticated:
        recently_visited_items = RecentlyVisitedItems.objects.filter(user_id = user_id, product__is_delete=False, product__is_active=True).order_by('-visited_at')
        for i in recently_visited_items:
            rating_avg[i.product_id] = 0
    else:
        recently_visited_items = []

    for i in what_is_new:
        rating_avg[i.id] = 0

    for key in rating_avg:
        avg = Review.objects.filter(shopproduct_id=key).aggregate(avg_rating = Avg('rating'))
        rating_avg[key] = avg.get('avg_rating')
        
    primary_image = ShopProductImage.objects.filter(shop_product__is_active = True, shop_product__is_delete = False)
    other_images = ShopProductImageSubTable.objects.filter(shop_product_image__shop_product__is_active=True, shop_product_image__shop_product__is_delete=False)
    subscription_data=Subscription.objects.all()
    product_imagine_data = ProductImagine.objects.all()
    site_url = settings.SITE_URL
    return render(request, 'index.html', {'site_url': site_url, 'recently_visited_items': recently_visited_items, 'primary_image': primary_image, 'other_images': other_images, 'what_is_new': what_is_new, 'slider':slider_data ,'product_shop_data': product_shop_data,'subscription_data':subscription_data , 'product_imagine_data': product_imagine_data, 'rating_avg': rating_avg})


def about_us(request):
    about_us_data = AboutUs.objects.get(id = 1)
    return render(request, 'pages/about-us.html', {'about_us_data': about_us_data})

  
def contact_us(request):
    try:
        try:  
           contact_us_details = ContactUsDetails.objects.get(default_address = True)
        except:
            contact_us_details = None
        contact_us_content = ContectUsContent.objects.get(id = 1)
        if request.method == "POST":
            try:
                name = request.POST.get('name')
                email = request.POST.get('email').lower()
                subject = request.POST.get('subject')
                description = request.POST.get('description')
                if not description:
                    messages.error(request, 'Please Enter Message')
                    return render(request, 'pages/contact-us.html', {'name': name, 'email': email, 'subject': subject, 'contact_us_details': contact_us_details })
                
                contact_us = ContactUsInquiry.objects.create(name=name, email=email, subject=subject, inquiry=description )
                contact_us.save()
                time = timezone.now()
                notification_message = f"{name} sent you an inquiry"
                Notification.objects.create(sender = email, receiver = contact_us_details.email.lower(), recevied_at = time, message = notification_message, notification_type = 'INQUIRY')
                message = "Hi, " + "Megadolls" + "," + description
                subject, from_email, to = "User's Inquiry",email, contact_us_details.email.lower()
                msg = EmailMultiAlternatives(subject, message, from_email, [to] )
                msg.send()
                messages.success(request, 'Message Sent')
                return redirect('contact_us')
            except:
                messages.error(request, 'Something Went Wrong')
                return redirect('home')     
        return render(request, 'pages/contact-us.html', {'contact_us_details': contact_us_details, 'contact_us_content': contact_us_content})
    except:
        messages.error(request, 'Something Went Wrong')
        return redirect('home')    


def faq(request):
    data=FAQ.objects.all()
    return render(request, 'pages/faq.html',{'data':data})


def privacy_policy(request):
    data=privacy.objects.all()
   
    return render(request, 'pages/privacy-policy.html',{'data':data})


def shipping_return_policy(request):
    return render(request, 'pages/shipping-return-policy.html')


def term_condition(request):
    data=TermsCondition.objects.all()
 
    return render(request, 'pages/term-condition.html',{'terms_data':data})


def category_subcategory_dropdown(request):
    # drop_down = ''
    drop_down = {}
    categories = Category.objects.filter(is_active=True)
    subcategories = SubCategory.objects.filter(category__is_active=True, is_active=True)
    i = 0
    for category in categories:
        cat_name = category.name
        drop_down[i] = f'<a class = "header-links dropdown-toggle" href = "#" role = "button" id = "dropdownMenuLink" data-bs-toggle = "dropdown" aria-expanded = "false" >{ cat_name }</a><ul class="dropdown-menu" aria-labelledby="dropdownMenuLink">'
        # drop_down += f'<li class = "dropdown" ><a class = "header-links dropdown-toggle" href = "#" role = "button" id = "dropdownMenuLink" data-bs-toggle = "dropdown" aria-expanded = "false" >{ cat_name }</a><ul class="dropdown-menu" aria-labelledby="dropdownMenuLink">'

        for subcategory in subcategories:
            if category.id == subcategory.category_id:
                drop_down[i] += f'<li><a class="dropdown-item" href="/{ subcategory.url }">{ subcategory.name }</a></li>'
                # drop_down += f'<li><a class="dropdown-item" href="{ subcategory.url }">{ subcategory.name }</a></li>'
        drop_down[i] += '</ul >'
        # drop_down += '</ul ></li >'
        i+=1
    return JsonResponse(drop_down, safe=False)


def create(request):
    products = ImagineProduct.objects.filter(is_active=True, is_delete=False, subcategory__name='Create')
    product_images = ImagineProductImage.objects.all()
    image_sub_tables = ImagineProductImageSubTable.objects.all()
    dress_types = DressType.objects.filter(is_active=True)
    colors = ProductColor.objects.filter(is_active=True)
    subcategory = SubCategory.objects.get(id=4, category__name="Imagine")
    return render(request, 'pages/create.html', {'imagine_products': products, 'imagine_product_images': product_images, 'image_sub_tables': image_sub_tables, 'dress_types': dress_types, 'colors': colors, 'subcategory': subcategory, 'site_url': settings.SITE_URL})


def play_color(request, id):
    imagine_product = ImagineProduct.objects.get(id=id, is_delete=False)
    imagine_product_images = ImagineProductImage.objects.get(imagine_product=id)
    image_sub_tables = ImagineProductImageSubTable.objects.filter(
        imagine_product_image_id=imagine_product_images.id)
    return render(request, 'pages/play-color.html', {'imagine_product': imagine_product, 'imagine_product_images': imagine_product_images, 'image_sub_tables': image_sub_tables})


def play(request):
    products = ImagineProduct.objects.filter(is_active=True, is_delete=False, subcategory__name='Play').order_by('-id')
    product_images = ImagineProductImage.objects.all()
    image_sub_tables = ImagineProductImageSubTable.objects.all()
    colors = ProductColor.objects.filter(is_active=True)
    dress_types = DressType.objects.filter(is_active=True)
    subcategory = SubCategory.objects.get(id=5, category__name="Imagine")
    return render(request, 'pages/play.html', {'products': products, 'product_images': product_images, 'image_sub_tables': image_sub_tables, 'colors': colors, 'dress_types': dress_types, 'subcategory': subcategory, 'site_url': settings.SITE_URL})


def imagine_detail(request, slug):
    try:
        imagine_product = ImagineProduct.objects.get(is_active=True, is_delete=False, slug=slug)
        favorite_product = None
        if Favorite.objects.filter(user_id=request.user.id, imagine_id=imagine_product.id).exists():
            favorite_product = Favorite.objects.get(user_id=request.user.id, imagine_id=imagine_product.id)
        related_products = None
        related_product_imgs = None
        related_product_img_list = None

        if imagine_product.related_product_list:
            product_list = string_to_list(imagine_product.related_product_list)
            related_products = ShopProduct.objects.filter(id__in=product_list, is_delete=False)
            related_product_imgs = ShopProductImage.objects.filter(shop_product_id__in=product_list)
            related_product_img_list = ShopProductImageSubTable.objects.all()

        imagine_product_image = ImagineProductImage.objects.get(
            imagine_product__is_active=True, imagine_product_id=imagine_product.id)

        image_sub_table = ImagineProductImageSubTable.objects.filter(
            imagine_product_image__imagine_product__is_active=True, imagine_product_image_id=imagine_product_image.id)

        return render(request, 'pages/create-detail.html', {'product': imagine_product, 'image': imagine_product_image, 'image_list': image_sub_table, 'related_products': related_products, 'related_product_imgs': related_product_imgs, 'related_product_img_list': related_product_img_list, 'favorite_product': favorite_product, 'site_url': settings.SITE_URL})
    except Exception as err:
        messages.error(request, "Something Went Wrong")
        imagine_product = ImagineProduct.objects.filter(is_active=True, slug=slug).order_by('-id')
        if imagine_product[0].subcategory.name == 'Play':
            return redirect('play')
        
        return redirect('create')


def web_imagine_filter(request, subcategory, slug):
    try:
        colors = ProductColor.objects.filter(is_active=True)
        dress_types = DressType.objects.filter(is_active=True)
        selected_color = None
        selected_dress_type = None
        
        imagine_products = ImagineProduct.objects.filter(is_active=True, is_delete=False).order_by('-id')
        
        if subcategory == 'play':
            if slug == 'color_all':
                selected_color = slug
                return redirect('play')
            
            selected_color = ProductColor.objects.get(url_slug=slug)
            imagine_products = imagine_products.filter(product_color_id=selected_color.id)
            template = 'pages/play-color.html'

        elif subcategory == 'create':
            if slug == 'dress_type_all':
                selected_dress_type = slug
                return redirect('create')
            
            selected_dress_type = DressType.objects.get(url_slug=slug)
            imagine_products = imagine_products.filter(dress_type_id=selected_dress_type.id)
            template = 'pages/create.html'

        imagine_product_images = ImagineProductImage.objects.filter(imagine_product__is_active=True, imagine_product__is_delete=False)
        image_sub_tables = ImagineProductImageSubTable.objects.filter(
            imagine_product_image__imagine_product__is_active=True, imagine_product_image__imagine_product__is_delete=False)

        return render(request, template, {'imagine_products': imagine_products, 'imagine_product_images': imagine_product_images, 'image_sub_tables': image_sub_tables, 'colors': colors, 'selected_color': selected_color, 'subcategory_name': subcategory, 'dress_types': dress_types, 'selected_dress_type': selected_dress_type})
    except Exception as err:
        if subcategory == 'Play':
            return redirect('play')

        return redirect('create')


def shop_product_data(subcategory_id=None):
    if(subcategory_id):
        subcategory_data = SubCategory.objects.get(id = subcategory_id)
        shop_products = ShopProduct.objects.filter(is_active=True, is_delete=False ,subcategory__id=subcategory_id).order_by('-id')

        shop_product_images = ShopProductImage.objects.filter(
            shop_product__is_active=True, shop_product__is_delete=False, shop_product__subcategory__id=subcategory_id)

        image_sub_tables = ShopProductImageSubTable.objects.filter(
            shop_product_image__shop_product__is_active=True, 
            shop_product_image__shop_product__is_delete=False, shop_product_image__shop_product__subcategory__id=subcategory_id)
        
    else:

        shop_products = ShopProduct.objects.filter(is_active=True, is_delete=False ,subcategory__id__in=[1, 2, 3]).order_by('-id')

        shop_product_images = ShopProductImage.objects.filter(
            shop_product__is_active=True, shop_product__is_delete=False, shop_product__subcategory__id__in=[1, 2, 3])

        image_sub_tables = ShopProductImageSubTable.objects.filter(
            shop_product_image__shop_product__is_active=True, 
            shop_product_image__shop_product__is_delete=False, shop_product_image__shop_product__subcategory__id__in=[1, 2, 3])

    collections = ProductCollection.objects.filter(is_active=True)
    subcategories = SubCategory.objects.filter(category__name="Shop")
    shop_products_data = ShopProduct.objects.filter(is_active=True, is_delete=False)
    collections_for_filter = ProductCollection.objects.filter(is_active=True, id__in=shop_products_data.values_list('product_collection_id', flat=True))
    subcategories_for_filter = SubCategory.objects.filter(id__in=shop_products_data.values_list('subcategory_id', flat=True)) 
    return {'subcategory_data':subcategory_data, 'subcategories_for_filter': subcategories_for_filter, 'collections_for_filter': collections_for_filter, 'shop_products': shop_products, 'shop_product_images': shop_product_images, 'image_sub_tables': image_sub_tables, 'collections': collections, 'subcategories': subcategories}


def shop_dolls_sets(request):
    try:
        data = shop_product_data(2)
        tmp = {}
        for i in data.get('shop_products'):
            avg=Review.objects.filter(shopproduct_id=i.id).aggregate(Avg('rating'))
            tmp[i.id] = avg.get('rating__avg')
        data['rating_avg'] = tmp
        data['site_url'] = settings.SITE_URL
        return render(request, 'pages/shop-dolls-sets.html', data)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect(request.META.get('HTTP_REFERER'))


def shop_dolls(request):
    try:
        data = shop_product_data(1)
        tmp = {}
        for i in data.get('shop_products'):
            avg=Review.objects.filter(shopproduct_id=i.id).aggregate(Avg('rating'))
            tmp[i.id] = avg.get('rating__avg')

        data['rating_avg'] = tmp
        data['site_url'] = settings.SITE_URL
        return render(request, 'pages/shop-dolls.html', data)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect(request.META.get('HTTP_REFERER'))


def shop_dress_sets(request):
    try:
        data = shop_product_data(3)
        tmp = {}
        for i in data.get('shop_products'):
            avg=Review.objects.filter(shopproduct_id=i.id).aggregate(Avg('rating'))
            tmp[i.id] = avg.get('rating__avg')
        data['rating_avg'] = tmp
        data['site_url'] = settings.SITE_URL
        return render(request, 'pages/shop-dress-sets.html', data)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect(request.META.get('HTTP_REFERER'))
        

def shop_detail_data(slug):
    shop_product = ShopProduct.objects.get(is_active=True, slug=slug)
    shop_product_image = ShopProductImage.objects.get(
        shop_product__is_active=True, shop_product_id=shop_product.id)
    image_sub_table = ShopProductImageSubTable.objects.filter(
        shop_product_image__shop_product__is_active=True, shop_product_image_id=shop_product_image.id)
    
    return {'product': shop_product, 'image': shop_product_image, 'image_list': image_sub_table}


# @login_required(login_url='web_login')
def shop_doll_detail(request, slug):
    try:
        data = shop_detail_data(slug)
        id = data.get('product').id
        if request.user.is_authenticated:
            user_id = request.user.id
            data['wishlist_product'] = Wishlist.objects.filter(user_id=user_id, shop_id=id).exists()

            recently_visited_item_data = RecentlyVisitedItems.objects.filter(user_id = user_id)
            if not recently_visited_item_data.filter(product_id = id).exists():  
                if recently_visited_item_data.count() >= 4:
                    item = recently_visited_item_data[:1][0] 
                    item.product_id = id  
                    item.save()
                else:
                    RecentlyVisitedItems.objects.create(user_id = user_id, product_id = id) 
            else:
                recent_item = RecentlyVisitedItems.objects.get(user_id = user_id, product_id = id)
                recent_item.visited_at = timezone.now()
                recent_item.save()
            
            # this is to check if use purchase product or not
            data['is_user_purchased'] = ProductOrderData.objects.filter(product_order__user_id=user_id, shop_product_id=id).exists()
        
        all_review=Review.objects.filter(shopproduct_id=id)
        object_review = all_review[:3]
        total_review=all_review.count() 
        data['object_review']=object_review
        data['total_review']=total_review
        
        cart_obj = get_cart_obj(request)
        data['cart_item'] = False
        if cart_obj:
            shop_product_list = string_to_list(cart_obj.shop_product_list)
            if data['product'].id in shop_product_list:
                data['cart_item'] = True

        if Review.objects.filter(shopproduct_id=id).exists():
            avg=Review.objects.filter(shopproduct_id=id).aggregate(Avg('rating')) # for the average rating
            data['rating__avg'] = round(avg.get('rating__avg'), 0)       # round fuction is used for round value of rating 
        data['site_url'] = settings.SITE_URL
        return render(request, 'pages/doll-detail.html', data)
    except Exception as err:
        messages.error(request, 'Something Went Wrong')
        return redirect(request.META.get('HTTP_REFERER'))
                
                
def web_shop_filter(request):
    # try:
        collection_id = request.POST.get('collections')
        sort_price = request.POST.get('sort')
        subcategory_name = request.POST.get('subcategory_name')
        subcategory_filter = request.POST.get('subcategory_filter')

        if subcategory_filter == '1':
            template = 'pages/shop-dolls.html'
        elif subcategory_filter == '2':
            template = 'pages/shop-dolls-sets.html'
        elif subcategory_filter == '3':
            template = 'pages/shop-dress-sets.html'
        else:
            return redirect(request.META.get('HTTP_REFERER'))

        order = 'offer_price'
        if sort_price == '2':
            order = '-offer_price'

        shop_products = ShopProduct.objects.filter(is_active=True, is_delete = False).order_by(order)
        if collection_id:
            shop_products = shop_products.filter(product_collection_id=collection_id)
        
        if subcategory_filter:
            shop_products = shop_products.filter(subcategory_id=subcategory_filter)
            
        # else:
        #     shop_products = shop_products.filter(subcategory__name=subcategory_name)

        shop_products_data = ShopProduct.objects.filter(is_active=True, is_delete=False)
        collections_for_filter = ProductCollection.objects.filter(is_active=True, id__in=shop_products_data.values_list('product_collection_id', flat=True))
        subcategories_for_filter = SubCategory.objects.filter(id__in=shop_products_data.values_list('subcategory_id', flat=True))
        shop_product_images = ShopProductImage.objects.filter(shop_product__is_active=True, shop_product__is_delete=False)
        image_sub_tables = ShopProductImageSubTable.objects.filter(shop_product_image__shop_product__is_active=True, shop_product_image__shop_product__is_delete = False)
        collections = ProductCollection.objects.filter(is_active=True)
        subcategories = SubCategory.objects.filter(category__name="Shop")
        return render(request, template, 
            {
                'collections_for_filter': collections_for_filter, 
                'subcategories_for_filter': subcategories_for_filter, 
                'shop_products': shop_products, 
                'shop_product_images': shop_product_images, 
                'image_sub_tables': image_sub_tables, 
                'collections': collections, 
                'subcategories': subcategories
            }
        )
    # except:
        # messages.error(request, "Something Went Wrong")
        # return redirect(request.META.get('HTTP_REFERER'))

def collection_according_subcategory_and_product(request):
    subcategory_id = request.GET.get('subcategory_id')
    shop_products = list(ShopProduct.objects.filter(is_active=True, is_delete=False, subcategory_id=subcategory_id).distinct('product_collection_id').values('product_collection_id', 'product_collection__name'))
    return JsonResponse({'collections': shop_products})


def add_to_cart_anonymous(request, product_id):
    if request.session.has_key('anonymous_user'):
        a_id = request.session['anonymous_user']['a_id']
        if AnonymousCart.objects.filter(a_id=a_id).exists():
            try:
                anony_cart = AnonymousCart.objects.get(a_id=a_id)

                shop_product_list = string_to_list(anony_cart.shop_product_list)
                shop_product_list.append(product_id)

                anony_cart.shop_product_list = shop_product_list
                anony_cart.save()
            except:
                a_id = generate_anonymous_id()
                request.session['anonymous_user'] = {'a_id': a_id}
                AnonymousCart.objects.create(a_id=a_id, shop_product_list=[product_id])
        else:
            a_id = generate_anonymous_id()
            request.session['anonymous_user'] = {'a_id': a_id}
            AnonymousCart.objects.create(a_id=a_id, shop_product_list=[product_id])
    else:
        a_id = generate_anonymous_id()
        request.session['anonymous_user'] = {'a_id': a_id}
        AnonymousCart.objects.create(a_id=a_id, shop_product_list=[product_id])

def anonymous_cart_item_count(request):
     cart = get_cart_obj(request)
     item_count = 0
     if cart:
        shop_product_list = string_to_list(cart.shop_product_list)
        shop_products = ShopProduct.objects.filter(id__in=shop_product_list, is_active=True)
        item_count = len(shop_products)
     return JsonResponse({'count': item_count}, safe=False)

            
        
def add_to_cart_user(request, product_id):
    user_id = request.user.id
    if UserCart.objects.filter(user_id=user_id).exists():
        user_cart = UserCart.objects.get(user_id=user_id)
        shop_product_list = string_to_list(user_cart.shop_product_list)
        shop_product_list.append(product_id)
        user_cart.shop_product_list = shop_product_list
        user_cart.save()
    else:
        product_list = []
        product_list.append(product_id)
        UserCart.objects.create(user_id=user_id, shop_product_list=product_list)


def user_cart_item_count(request):
    try:
        cart = get_cart_obj(request)
        shop_product_list = string_to_list(cart.shop_product_list)
        shop_products = ShopProduct.objects.filter(id__in=shop_product_list, is_active=True).values_list('id', flat=True)
        shero_dolls_list = string_to_list(cart.shero_dolls_list)
        shero_products = SheroDolls.objects.filter(id__in=shero_dolls_list, is_active=True).values_list('id', flat=True)
        item_count = len(shop_products) + len(shero_products)
        return JsonResponse({'count': item_count}, safe=False)
    except:
        return JsonResponse({'count': 0}, safe=False)


        
# @login_required(login_url='web_login')
def add_shero_to_cart(request, slug):
    if request.user.is_anonymous:
        messages.error(request, "You Need To Login First To Buy Shero Dolls")
        return redirect('buy_shero_dolls', slug)
    user_subscription_data = UserSubscriptions.objects.get(user_id = request.user.id)
    if user_subscription_data.subscription_id:
        shero = SheroDolls.objects.get(slug=slug)
        shero_id = shero.id
        user_id = request.user.id
        if UserCart.objects.filter(user_id=user_id).exists():
            user_cart = UserCart.objects.get(user_id=user_id)
            shero_dolls_list = string_to_list(user_cart.shero_dolls_list)
            shero_dolls_list.append(shero_id)
            user_cart.shero_dolls_list = shero_dolls_list
            user_cart.save()
        else:
            product_list = []
            product_list.append(shero_id)
            UserCart.objects.create(user_id=user_id, shero_dolls_list=product_list)
        messages.success(request, "Added to Cart")
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, "Please Buy Subscription Plan First to Buy Shero Dolls")
        return redirect('buy_shero_dolls', slug)





def get_shop_product_id(slug):
    product_data = ShopProduct.objects.get(is_active=True, slug=slug)
    return product_data.id

#  check quantity of a particular product which is in cart
def check_quantity(request, product_id):
    cart = get_cart_obj(request)
    if cart:
        shop_product_list = string_to_list(cart.shop_product_list)
        product = ShopProduct.objects.get(id = product_id, is_active=True)
        return product.quantity > shop_product_list.count(product_id)
    else:
        product = ShopProduct.objects.get(id = product_id, is_active=True)
        return product.quantity > 0


# check quantity of all product which is in the cart
def check_all_quantity(request):
    cart = get_cart_obj(request)
    if cart:
        shop_product_list = string_to_list(cart.shop_product_list)
        products = ShopProduct.objects.filter(id__in = shop_product_list)
        for product in products:
            if product.quantity < shop_product_list.count(product.id):
                name = product.name
                raise Exception(f"{name} is not have Required Quantity")
    return None


def add_to_cart(request, slug):
    try:
        product_id = get_shop_product_id(slug)
        quantity_check = check_quantity(request, product_id)
        if quantity_check == False:
            messages.error(request, NO_STOCK_MSG)
            return redirect('shop_doll_detail', slug)
            
        if request.user.is_anonymous:
            add_to_cart_anonymous(request, product_id)
        else:
            add_to_cart_user(request, product_id)
        messages.success(request, 'Product Added to cart')
    except:
        messages.error(request, 'Something Went Wrong')
        
    return redirect('shop_doll_detail', slug)

# @login_required(login_url='web_login')
def buy_now(request, slug):
    try:
        product_id = get_shop_product_id(slug)
        
        quantity_check = check_quantity(request, product_id)
        if quantity_check == False:
            messages.error(request, NO_STOCK_MSG)
            return redirect('shop_doll_detail', slug)

        if request.user.is_authenticated:
            add_to_cart_user(request, product_id)
        else:
            add_to_cart_anonymous(request, product_id)

        return redirect('view_cart')
    except Exception as err:
        messages.error(request, 'Something Went Wrong')
        return redirect('shop_doll_detail', slug)

# @login_required(login_url='web_login')
def buy_now_shero_dolls(request, slug):
    if request.user.is_anonymous:
        messages.error(request, "You Need to Login First to buy Shero Dolls")
        return redirect('buy_shero_dolls', slug)

    user_subscription_data = UserSubscriptions.objects.get(user_id = request.user.id)
    if user_subscription_data.subscription_id:
        product_id = SheroDolls.objects.get(slug = slug).id
        user_id = request.user.id
        if  UserCart.objects.filter(user_id = user_id).exists():
            user_cart = UserCart.objects.get(user_id = user_id)
            shero_list = user_cart.shero_dolls_list 
            shero_dolls = string_to_list(shero_list)
            shero_dolls.append(product_id)
            user_cart.shero_dolls_list = shero_dolls
            user_cart.save()
        else:
            shero_dolls_list = []
            shero_dolls_list.append(product_id)
            UserCart.objects.create(user_id = user_id, shero_dolls_list=shero_dolls_list)
        return redirect('view_cart')
    else:
        messages.error(request, "Please Buy Subscription Plan First to Buy Shero Dolls")
        return redirect('buy_shero_dolls', slug)



def wishlist_add_to_cart(request, slug):
    try:
        product_id = get_shop_product_id(slug)
        if not check_quantity(request, product_id):
            messages.error(request, NO_STOCK_MSG)
            return redirect('view_wishlist')
        
        if request.user.is_anonymous:
            add_to_cart_anonymous(request, product_id)
        else:
            add_to_cart_user(request, product_id)
            Wishlist.objects.filter(user_id=request.user.id, shop__slug=slug).delete()
            messages.success(request, 'Product Added to cart')
    except:
        messages.error(request, 'Something Went Wrong')
    return redirect('view_wishlist')

def get_cart_obj(request):
    cart = None
    if request.user.is_anonymous:
        if request.session.has_key('anonymous_user'):
            id = request.session['anonymous_user']['a_id']
            if AnonymousCart.objects.filter(a_id=id).exists():
                return AnonymousCart.objects.get(a_id=id)
    else:
        id = request.user.id
        if UserCart.objects.filter(user_id=id).exists():
            return UserCart.objects.get(user_id=id)
    return None


def empty_cart(request):
    cart = get_cart_obj(request)
    cart.delete()
    return redirect('view_cart')


def remove_item(request, product_id):
    cart = get_cart_obj(request)
    shop_product_list = string_to_list(cart.shop_product_list)
    new_list = list(filter(lambda id: id != product_id, shop_product_list))
    cart.shop_product_list = new_list
    cart.save()
    return redirect('view_cart')

def remove_shero_dolls(request, shero_id):
    cart = get_cart_obj(request)
    shero_dolls_list = string_to_list(cart.shero_dolls_list)
    new_list = list(filter(lambda id: id != shero_id, shero_dolls_list))
    cart.shero_dolls_list = new_list
    cart.save()
    return redirect('view_cart')


def cart_sub_total(request):
    cart = get_cart_obj(request)
    shop_product_list = string_to_list(cart.shop_product_list)
    product_dict = dict(Counter(shop_product_list))
    product_ids = product_dict.keys()
    product_data = ShopProduct.objects.filter(id__in=product_ids)
    sub_total = 0

    for product in product_data:
        if product.offer_price > 0:
            sub_total += product.offer_price * product_dict[product.id]
        else:
            sub_total += product.original_price * product_dict[product.id]

    if cart and hasattr(cart, 'shero_dolls_list'):
        shero_dolls_list = string_to_list(cart.shero_dolls_list)
        if shero_dolls_list:
            shero_dolls_dict = dict(Counter(shero_dolls_list))
            shero_dolls_ids = shero_dolls_dict.keys()
            shero_dolls_data = SheroDolls.objects.filter(id__in=shero_dolls_ids)

            for product in shero_dolls_data:
                sub_total += product.original_price * shero_dolls_dict[product.id]

    if cart and hasattr(cart, 'offer') and cart.offer_id:
        discount_percentage = Decimal(cart.offer.percentage)
        after_discount_total = sub_total - ( sub_total * (discount_percentage / 100))
        return "{:.2f}".format(after_discount_total)

    return sub_total


# def charge_and_total(sub_total):
#     charges = {}
#     order_charges = OrderCharge.objects.all()
#     for order_charge in order_charges:
#         charges[order_charge.name] = sub_total * order_charge.percentage / 100
#         total = sub_total + charges[order_charge.name]
#         total = "{0:.2f}".format(total)
#     return {'order_charges': charges, 'total': total}


@csrf_exempt
def decrease_item_count(request):
    cart = get_cart_obj(request)
    product_id = int(request.POST.get('product_id'))
    if request.POST.get('is_shero'):
        shero_dolls_list = string_to_list(cart.shero_dolls_list)
        if len(shero_dolls_list) > 0:
            shero_dolls_list.remove(product_id)
        cart.shero_dolls_list = shero_dolls_list
        product_count = shero_dolls_list.count('product_id')
        quantity = SheroDolls.objects.get(id = product_id).quantity
        
    else:
        shop_product_list = string_to_list(cart.shop_product_list)
        product = ShopProduct.objects.get(id = product_id)
        quantity = product.quantity
        
        if len(shop_product_list) > 0:
            shop_product_list.remove(product_id)

        cart.shop_product_list = shop_product_list
        product_count = shop_product_list.count(product_id)
    cart.save()
    
    total = sub_total = cart_sub_total(request)
    # charges,  = charge_and_total(sub_total).values()
    
    return JsonResponse({'sub_total': sub_total, 'total': total, 'product_count': product_count, 'available_quantity': quantity})


@csrf_exempt
def increase_item_count(request):
    cart = get_cart_obj(request)
    product_id = int(request.POST.get('product_id'))
    if request.POST.get('is_shero'):
        shero_dolls_list = string_to_list(cart.shero_dolls_list)
        
        shero_count = shero_dolls_list.count(product_id)

        shero_dolls = SheroDolls.objects.get(id = product_id).quantity

        if shero_dolls < shero_count and shero_count > 3:
            return JsonResponse({'success': False, 'message': 'Required Quantity Not Available', 'product_count': shero_count, 'available_quantity': shero_dolls})
        shero_dolls_list.append(product_id)
        cart.shero_dolls_list = shero_dolls_list
        product_count = shero_dolls_list.count(product_id)
        quantity = shero_dolls

    else:
        shop_product_list = string_to_list(cart.shop_product_list)  
        product = ShopProduct.objects.get(id = product_id)
        
        product_count = shop_product_list.count(product_id)
   
        if (product_count + 1) > product.quantity:
            return JsonResponse({'success': False, 'message': 'Required Quantity Not Available', 'product_count': product_count, 'available_quantity': product.quantity})
        shop_product_list.append(product_id)
        cart.shop_product_list = shop_product_list
        product_count = shop_product_list.count(product_id)
        quantity = product.quantity

    cart.save()
    
    total = sub_total = cart_sub_total(request)
    # charges,  = charge_and_total(sub_total).values()
    # 'charges': charges,
    return JsonResponse({'sub_total': sub_total, 'total': total, 'product_count': product_count, 'available_quantity': quantity})


@csrf_exempt
def decrease_shero_count(request):
    cart = get_cart_obj(request)
    shero_dolls_list = string_to_list(cart.shero_dolls_list)
    product_id = int(request.POST.get('product_id'))
    product = SheroDolls.objects.get(id = product_id)
    if len(shero_dolls_list) > 0:
        shero_dolls_list.remove(product_id)
    cart.shero_dolls_list = shero_dolls_list
    cart.save()
    total = sub_total = cart_sub_total(request)
    # charges,  = charge_and_total(sub_total).values()
    product_count = shero_dolls_list.count(product_id)
    
    return JsonResponse({'sub_total': sub_total, 'total': total, 'product_count': product_count, 'available_quantity': product.quantity})


@csrf_exempt
def increase_shero_count(request):
    cart = get_cart_obj(request)
    shero_dolls_list = string_to_list(cart.shero_dolls_list)

    product_id = int(request.POST.get('product_id'))
    
    product = SheroDolls.objects.get(id = product_id)
    
    product_count = shero_dolls_list.count(product_id)
    if product.quantity <= product_count:
        return JsonResponse({'success': False, 'message': 'Required Quantity Not Available', 'product_count': product_count, 'available_quantity': product.quantity})
    
    shero_dolls_list.append(product_id)
    
    cart.shero_dolls_list = shero_dolls_list
    cart.save()
    
    total = sub_total = cart_sub_total(request)
    # charges,  = charge_and_total(sub_total).values()
    product_count = shero_dolls_list.count(product_id)
    # 'charges': charges,
    return JsonResponse({'sub_total': sub_total, 'total': total, 'product_count': product_count, 'available_quantity': product.quantity})    


# Only show vaild offer:
def get_valid_offer(user_id):
    # get usedoffer object which is used
    used_offer = UsedOffer.objects.filter(user_id = user_id, is_used=True)

    # append ids of used_offer 
    offer_ids = []
    for i in used_offer:
        offer_ids.append(i.offer_id)

    # exclude those ids which is in the offer_ids list
    #  to get only those offer only which is not used
    offers=Offer.objects.filter(is_active=True).exclude(id__in=offer_ids)
    return offers

# @login_required(login_url='web_login')
def view_cart(request):
    if request.session.has_key('guest_user'):
        del request.session['guest_user']
        request.session.modified = True

    id = request.user.id
    shop_products = None
    shop_product_imgs = None
    product_dict = {}
    sub_total = 0
    total = 0
    data = {}
    rating_dict={}
    may_like_product = None

    try:
        cart = get_cart_obj(request)
        shop_product_list = []
        shero_dolls_list = []
        is_any_out_of_stock = False
        if cart :
            shop_product_list = string_to_list(cart.shop_product_list)
            is_any_out_of_stock = ShopProduct.objects.filter(is_active=True, is_delete=False, id__in=shop_product_list, quantity=0).exists()
        
            if request.user.is_authenticated:
                shero_dolls_list = string_to_list(cart.shero_dolls_list)
            
        product_dict = dict(Counter(shop_product_list))
        product_ids = product_dict.keys()
        shero_dict = dict(Counter(shero_dolls_list))
        shero_ids = shero_dict.keys()


        all_product = ShopProduct.objects.filter(is_active=True, is_delete = False)
        all_shero_dolls = SheroDolls.objects.filter(is_active = True)

        # collections = ProductCollection.objects.filter(is_active=True)
        # subcategories = SubCategory.objects.filter(category__name="Shop")

        if all_product:
            offset = randint(1, all_product.filter(quantity__gte=1).count())
            may_like_product = all_product.filter(quantity__gte=1)[offset:offset+4]
        
        may_like_product_list = []
        for product in may_like_product:
            avg = Review.objects.filter(shopproduct_id=product.id).aggregate(Avg('rating'))
            product.average_rating = avg.get('rating__avg')
            product.save()
            may_like_product_list.append(product.id)


        may_like_product_images = ShopProductImage.objects.filter(shop_product_id__in=may_like_product_list)
        may_like_product_sub_images = ShopProductImageSubTable.objects.all()
        
        shop_products = all_product.filter(id__in=product_ids)
        shero_dolls = all_shero_dolls.filter(id__in = shero_ids)
        
        wishlist_item_ids = Wishlist.objects.filter(user_id=id).values_list('shop_id', flat=True)

        for product in shop_products:
            if product.offer_price > 0:
                sub_total += product.offer_price * product_dict[product.id]
            else:
                sub_total += product.original_price * product_dict[product.id]
        
        shop_product_imgs = ShopProductImage.objects.filter(
            shop_product_id__in=product_ids)
        shero_dolls_images = SheroDollsImage.objects.filter(shero_dolls_id__in = shero_ids)
        

        total = sub_total

        valid_offers = get_valid_offer(id)
        data = {
            'shero_dolls': shero_dolls,
            'shero_dolls_images': shero_dolls_images,
            'shop_products': shop_products,
            'shop_product_imgs': shop_product_imgs,
            'product_dict': product_dict,
            'shero_dict': shero_dict,
            'sub_total': sub_total,
            'offers':valid_offers,
            'may_like_product': may_like_product,
            'may_like_product_images': may_like_product_images,
            'may_like_product_sub_images': may_like_product_sub_images,
            'total': total,
            'shop_product_list': shop_product_list,
            'wishlist_item_ids': wishlist_item_ids,
            'cart': cart,
            'is_any_out_of_stock': is_any_out_of_stock,
            'site_url': settings.SITE_URL,
        }
        return render(request, 'pages/cart.html', data)
    except Exception as err:
        return render(request, 'pages/cart.html', data)


def remove_from_wishlist(request, product_id):
    try:
        user_id = request.user.id
        wishlist_item = Wishlist.objects.filter(user_id=user_id, shop_id=product_id)
        if wishlist_item.exists():
            wishlist_item.delete()
            messages.success(request, "Removed from Wishlist")
    except:
        messages.error(request, "Failed to Remove from Wishlist")
    return redirect('view_cart')
    

def get_cart_product_data(request):
    try:
        cart = get_cart_obj(request)
    
        shop_product_list = string_to_list(cart.shop_product_list)
        
        shero_dolls_list = []
        if request.user.is_authenticated:
            shero_dolls_list = string_to_list(cart.shero_dolls_list)
        
        shero_dict = dict(Counter(shero_dolls_list))
        shero_ids = shero_dict.keys()
        product_dict = dict(Counter(shop_product_list))
        product_ids = product_dict.keys()
        shop_products = ShopProduct.objects.filter(id__in=product_ids, is_active=True, is_delete=False).values('id', 'name', 'offer_price', 'original_price', 'quantity')
        shero_dolls = SheroDolls.objects.filter(id__in = shero_ids, is_active=True).values('id', 'name', 'original_price', 'quantity' )

        cart_data = []
        for data in shop_products:
            cart_data.append(data)
            data['is_shero'] = False
            
        for data in shero_dolls:
            cart_data.append(data)
            data['is_shero'] = True
            
        for i in cart_data:
            if i['is_shero']:
                i['cart_quantity'] = shero_dict.get(i.get('id'))
            else:
                i['cart_quantity'] = product_dict.get(i.get('id'))
            
        data = {
            'cart_data': cart_data,
            'applied_offer': 0
        }

        if request.user.is_authenticated and cart.offer:
            data['applied_offer'] = cart.offer.percentage
        return JsonResponse(data, safe=False)
    except:
        return JsonResponse(None, safe=False)


@login_required(login_url='web_login')
def album_detail(request):
    return render(request, 'pages/album-detail.html')


@login_required(login_url='web_login')
def album(request):
    return render(request, 'pages/album.html')

def get_shipping_price_range(shipping_prices, sub_total):
    shipping_price_range = shipping_prices.order_by('order_value_from')
    for price_range in shipping_price_range:
        if float(sub_total) >= price_range.order_value_from and float(price_range.order_value_upto) > 0.00 and float(sub_total) <= price_range.order_value_upto and float(price_range.shipping_cost) > 0.00:
            return price_range
    return shipping_price_range.last()

@login_required(login_url='web_login')
def billing(request):
    try:
        if request.META.get('HTTP_REFERER') and not reverse('billing') in request.META.get('HTTP_REFERER'):
            if request.META.get('HTTP_REFERER') == None or not reverse('view_cart') in request.META.get('HTTP_REFERER'):
                return redirect('view_cart')
        
        user_id = request.user.id
        
        shipping_prices = ShippingPrice.objects.all()
        
        sub_total = cart_sub_total(request)
        shipping_price_range = get_shipping_price_range(shipping_prices, sub_total)
        
        # carrier_data = get_carriers()
        # carriers = json.loads(carrier_data.text)
        data = {
            # 'carriers': carriers, 
            'sub_total': sub_total,
            'addresses': UserAddress.objects.filter(user_id=user_id),
            'countries': WebCountry.objects.all(),
            'shipping_prices': shipping_prices,
            'shipping_price_range': shipping_price_range,
            # 'grand_total': round(float(sub_total) + float(shipping_price_range.shipping_cost), 2)
            'grand_total':round(float(sub_total) + float(shipping_price_range.shipping_cost) if shipping_price_range else 0.0, 2)
        }
        
        return render(request, 'pages/billing.html', data)
    except :
       
        messages.error(request, "Something Went Wrong")
        return redirect('view_cart')



# Blog Start
# to show detailed blog after clicking on blog
def blog_detail(request, slug):
    try:
        user = request.user.id
        try:
            user_data = User.objects.get(id = user)
        except:
            user_data = None
        now = timezone.now()
        blog = Blog.objects.get(slug=slug, is_publish=True, publish_at__lte=now)
        id = blog.id
        comment_data = BlogUser.objects.filter(user_id = user)
        login_user_comments = comment_data.filter(blog_id = id)
        comments = BlogUser.objects.filter(blog_id = id).exclude(user_id = user)
        total_comments = BlogComment.objects.filter(blog_id = id).count() 
        if request.method == "POST":
            comment = request.POST.get('comment')
            blog_comment = BlogComment.objects.create(comment=comment, user_id=user, blog_id=blog.id)
            BlogUser.objects.create(user_id=user, blog_id=id, comment_id=blog_comment.id)
            messages.success(request, 'Comment Posted')
            return redirect('blog_detail', slug)    
        return render(request, 'pages/blog/blog-detail.html', {'user_data': user_data, 'blog': blog,
         'login_user_comments': login_user_comments,
          'comments': comments, 'total_comments' : total_comments,
          'site_url': settings.SITE_URL})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("blog")

# to edit user's comment on blog
@login_required(login_url='web_login')
def edit_blog_comment(request, id):
    comment = BlogComment.objects.get(id=id)
    blog_id = comment.blog.id
    blog_data = Blog.objects.get(id = blog_id)
    slug = blog_data.slug 
    try:
        new_comment = request.POST.get("comment")
        if new_comment:
            if len(new_comment) >= 1000:
                messages.error(request, "Words Limit 255")
                return redirect('blog_detail', slug)
            else:    
                comment.comment = new_comment
                comment.save() 
                messages.success(request, "Comment Edited")
                return redirect('blog_detail', slug)
        else:
            messages.error(request, "Please Enter Comment")
            return redirect('blog_detail', slug)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('blog_detail', slug)    

# to show blog
def blog(request):
    try:
        blog_content = BlogContent.objects.get(id = 1)
        now = timezone.now()
        links = LinksOnBlog.objects.filter(is_active = True, is_social = False)
        social_links = LinksOnBlog.objects.filter(is_active = True, is_social = True)
        blogs = Blog.objects.filter(is_publish=True, publish_at__lte=now).order_by('-id')
        cat_and_subcat = {}
        for i in blogs: 
            if cat_and_subcat.get(i.blog_category.name):
                cat_and_subcat[i.blog_category.name].append({'blog_slug': i.slug, 'blog_heading': i.heading})
            else:
                cat_and_subcat[i.blog_category.name] = [{'blog_slug': i.slug, 'blog_heading': i.heading}]

        p = Paginator(blogs, per_page=4)  # creating a paginator object
        # getting the desired page number from url
        page_number = request.GET.get('page')
        try:
            page_obj = p.get_page(page_number)  # returns the desired page objectdef blog
        except PageNotAnInteger:
            # if page_number is not an integer then assign the first page
            page_obj = p.page(1)
        except EmptyPage:
            # if page is empty then return last page
            page_obj = p.page(p.num_pages)
        
        return render(request, 'pages/blog/blog.html', {'blogs': blogs, 'cat_and_subcat': cat_and_subcat, 'blog_content': blog_content, 'page_obj': page_obj, 'links': links, 'social_links': social_links})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("home")

# to search blog on blog page     
def search_in_blog(request):
    try:
        if request.method == "GET":
            text = request.GET.get('text')
            if text:
                blog_content = BlogContent.objects.get(id = 1)
                links = LinksOnBlog.objects.filter(is_active = True, is_social = False)
                social_links = LinksOnBlog.objects.filter(is_active = True, is_social = True)
                subcategory_data = BlogSubCategory.objects.all()
                category_data = BlogCategory.objects.all()
                now = timezone.now()
                blogs = Blog.objects.filter(is_publish=True, publish_at__lte=now)
                now = timezone.now()
                data = Blog.objects.filter(heading__icontains=text, is_publish=True, publish_at__lte=now) | Blog.objects.filter(content__icontains=text, is_publish=True, publish_at__lte=now) 
                p = Paginator(data, per_page=4) 
                page_number = request.GET.get('page')
                page_obj = p.get_page(page_number)
                return render(request, 'pages/blog/blog.html', {'blog_content': blog_content, 'blogs': blogs, 'page_obj': page_obj, 'category_data': category_data, 'subcategory_data': subcategory_data, 'links': links, 'social_links': social_links}) 
            else:
                return redirect("blog")    
        else:
            return redirect("blog")    
    except PageNotAnInteger:
        page_obj = p.page(1)
    except EmptyPage:
        page_obj = p.page(p.num_pages)
    except:
        messages.error(request, "Something Went Wrong")     
        return redirect('blog')  


def blog_filter_by_subcategory(request, id):
    try:
        blog_content = BlogContent.objects.get(id = 1)
        subcategory_data = BlogSubCategory.objects.all()
        category_data = BlogCategory.objects.all()
        now = timezone.now()
        links = LinksOnBlog.objects.filter(is_active = True, is_social = False)
        social_links = LinksOnBlog.objects.filter(is_active = True, is_social = True)

        blogs = Blog.objects.filter(is_publish=True, publish_at__lte=now, sub_category_id = id)
        p = Paginator(blogs, per_page=4)  # creating a paginator object
        # getting the desired page number from url
        page_number = request.GET.get('page')
        try:
            page_obj = p.get_page(page_number)  # returns the desired page objectdef blog
        except PageNotAnInteger:
           # if page_number is not an integer then assign the first page
            page_obj = p.page(1)
        except EmptyPage:
            # if page is empty then return last page
            page_obj = p.page(p.num_pages)
        
        return render(request, 'pages/blog/blog.html', {'blog_content': blog_content, 'blogs': blogs, 'category_data': category_data, 'subcategory_data': subcategory_data, 'page_obj': page_obj, 'links': links, 'social_links': social_links})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("blog")
   

# to delete user's comment 
def delete_blog_comment(request):
    try:
        id = request.POST.get('blog_comment')
        comment = BlogComment.objects.get(id=id)
        blog_id = comment.blog_id
        blog_data = Blog.objects.get(id = blog_id)
        slug = blog_data.slug       
        try:
            comment.delete() 
            messages.success(request, 'Comment Deleted')
            return redirect('blog_detail', slug)
        except:
            messages.error(request, "Something Went Wrong")
            return redirect('blog_detail', slug)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("blog") 

# Blog End               

# @login_required(login_url='web_login')
def cart(request):
    return render(request, 'pages/cart.html')

# User's address in my account start
@login_required(login_url='web_login')
def my_account_address(request):
    try:
        id = request.user.id
        user_address_data = UserAddress.objects.filter(user_id=id).order_by('-default_address')
        countries = WebCountry.objects.all()
        user_data = User.objects.get(id=id)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("home")
    
    return render(request, 'pages/my-account/my-account-address.html', {'user_data': user_data, 'user_address_data': user_address_data, 'countries': countries})


# @login_required(login_url='web_login')
@api_view(['GET'])
def get_states(request):
    country_id = request.GET.get('country_id')
    states_data = WebState.objects.filter(country_id=country_id)
    serializer = WebStateSerializer(states_data, many=True)
    return Response({'success': True, 'payload': serializer.data})


# @login_required(login_url='web_login')
@api_view(['GET'])
def get_cities(request):
    state_id = request.GET.get('state_id')
    cities_data = WebCity.objects.filter(state_id=state_id).order_by('name')
    serializer = WebCitySerializer(cities_data, many=True)
    return Response({'success': True, 'payload': serializer.data})


# to change default address of user in my account
@login_required(login_url='web_login')
def change_active_address(request, id):
    try:
        user_id = request.user.id
        active_address = UserAddress.objects.filter(default_address=True, user_id=user_id)
        if active_address.exists():
            active_address  = active_address.first()
            active_address.default_address = False
            active_address.save()
        address = UserAddress.objects.get(id=id)
        address.default_address = True
        address.save()
        messages.success(request, 'Default Address Changed')
    except:
        address = UserAddress.objects.get(id=id)
        address.default_address = True
        address.save()    
        messages.error(request, 'Failed to Change Address')
    return redirect('my_account_address')

# to delete user's address in my account
def delete_address(request):
    try:
        user_id = request.user.id 
        address_id = request.POST.get('address_id')
        UserAddress.objects.filter(id=address_id).delete()
        user_addresses = UserAddress.objects.filter(user_id=request.user.id).order_by('-id').first()
        messages.success(request, 'Address Deleted')
        user_address = UserAddress.objects.filter(user_id = user_id).count()
        if user_address >= 1:
            if not user_addresses.default_address:
                return redirect('change_active_address', user_addresses.id)
        return redirect('my_account_address')
    except:
        messages.error(request, 'Something went wrong')
        return redirect('my_account_address')
        


# to edit user's address in my account
def edit_address_data(request):
    try:
        if request.method == "POST":
            address_id = request.POST.get('address')
            address = UserAddress.objects.get(id=address_id)
            address.name = request.POST.get('name')
            address.house_num = request.POST.get('house_num', None)
            address.area_name = request.POST.get('area_name')
            address.web_country_id = request.POST.get('country')
            address.web_state_id = request.POST.get('state')
            address.web_city = request.POST.get('city')
            address.zip_code = request.POST.get('zipcode')
            address.save()
            messages.success(request, 'Address Updated')
            return redirect('my_account_address')
        else:
            address_id = request.GET.get('address_id')
            address = UserAddress.objects.get(id=address_id)
            address_serializer = UserAddressSerializer(address)
            states = WebState.objects.filter(country_id=address.web_country.id)
            state_serializer = WebStateSerializer(states, many=True)
            cities = WebCity.objects.filter(state_id=address.web_state.id)
            city_serializer = WebCitySerializer(cities, many=True)
        
        return JsonResponse({
            'address': address_serializer.data,
            'states': state_serializer.data,
            'cities': city_serializer.data
        })

    except:
        return JsonResponse({'success': False, "message": "Failed to Update Address"})


# to add new address of user in my account
def add_address(request):
    try:
        user_id = request.user.id
        default_address = True
        if UserAddress.objects.filter(user_id=user_id).exists():
            default_address = False

        user_address = UserAddress()
        user_address.name = request.POST.get('name') 
        user_address.house_num = request.POST.get('house_number', None) 
        user_address.area_name = request.POST.get('area_name') 
        user_address.web_country_id = request.POST.get('country') 
        user_address.web_city = request.POST.get('city') 
        user_address.web_state_id = request.POST.get('state') 
        user_address.zip_code = request.POST.get('zipcode')
        country_code = request.POST.get("country_code")
        mobile = request.POST.get('phone')
        mobile_number = f"{country_code}{mobile}" 
        user_address.phone = mobile_number
        user_address.user_id = user_id 
        user_address.default_address = default_address
        user_address.save()
        messages.success(request, "Address added successfully")
        return redirect('billing')
    except:
        return JsonResponse({
            "success": True,
            "message": "Failed to Add Address",
            "data": None
        })
    

# to show all addresses of user in my account
class UserAddressView(APIView):
    def get(self, request):
        try:
            user_id = request.GET['user_id']
            address_id = request.GET['address_id']
            # u = UserAddress.objects.get(user_id=user_id)
            if address_id:
                user_address = UserAddress.objects.get(id=address_id)
                serializer = UserAddressSerializer(user_address)
            else:
                user_address = UserAddress.objects.filter(user_id=user_id)
                serializer = UserAddressSerializer(user_address, many=True)
                # serializer1  = UserAddressSerializer(u, many=True)
            return Response({
                'status': True,
                'payload': serializer.data,
                # 'con': serializer1.data,              
                'message': 'Address Fetched Successfully'
            })
        except Exception as err:
            return Response({
                'status': False,
                'message': 'Something Went Wrong'
            })
 
    def post(self, request):
        # try:
            data = request.data
            user = data['user']
            user_data = UserAddress.objects.filter(user_id=user).exists()
            default_address = True
            if user_data:
                default_address = False
            # else:
            #     return Response({
            #     'status': False,
            #     'message': "Data not found",
            # })
            user_address = UserAddress.objects.create(user_id=data['user'], 
            area_name=data['area_name'], web_country_id=data['country'], web_state_id=data['state'], web_city=data['city'], 
            zip_code=data['zipcode'], house_num=data.get('house_number', None), name = data['name'], default_address=default_address)  
            messages.success(request, "Address Added")
            return redirect('my_account_address')
            # return Response({
            #     'status': True,
            #     'data': 'data',
            #     'message': 'Address Added Successfully'
            # })
        # except:
        #     return Response({
        #         'status': False,
        #         'message': "something went wrong",
        #     })

    def put(self, request):
        try:
            data = request.data
            UserAddress.objects.get(id=data['address_id'])
            serializer = UserAddressSerializer(data=data)

            if serializer.is_valid(raise_exception=False):
                

                user = serializer.save()
                messages.success(request, "Address Updated")
                return Response({
                    'status': True,
                    'message': 'Address Saved Successfuly'
                })
            else:
                return Response({
                'status': False,
                'message': serializer.errors,
            })
        except:
            return Response({
                'status': False,
                'message': "something went wrong",
            })

# User's address in my account end            


# @login_required(login_url='web_login')
def my_account_favorite(request):
    try:
        if request.user.is_authenticated and request.method == 'POST':
            product_id = request.POST.get('id')
            is_added = False
            user_id = request.user.id
            
            if Favorite.objects.filter(user_id=user_id, imagine_id=product_id).exists():
                Favorite.objects.filter(user_id=user_id, imagine_id=product_id).delete()
                msg = "Product Removed From Favorite"
            else:
                Favorite.objects.create(user_id=user_id, imagine_id=product_id)
                msg = "Product Added to Favorite"
                is_added = True

            return JsonResponse({'status': True, 'is_added': is_added, 'message': msg})
        else:
            return JsonResponse({'status':False , 'message':"You need to login first"})
    except:
        return JsonResponse({'status': False, 'message': "Something went wrong"})
    

def add_to_favorite_create_detail(request, id):
    if request.user.is_anonymous:
        return JsonResponse({'status':False , 'message':"You need to login first"})
    
    user_id = request.user.id
    if not Favorite.objects.filter(user_id=user_id, imagine_id=id).exists():
        Favorite.objects.create(user_id=user_id, imagine_id=id)
        return JsonResponse({'status': True, 'message': "product added to Favorite"})

    return JsonResponse({'status': True, 'message': "Product Already in Favorite"})


def remove_to_favorite_create_detail(request, id):
    if request.user.is_anonymous:
        return JsonResponse({'status':False , 'message':"You need to login first"})
    
    user_id = request.user.id
    if Favorite.objects.filter(user_id=user_id, imagine_id=id).exists():
        Favorite.objects.filter(user_id=user_id, imagine_id=id).delete()
        return JsonResponse({'status': True, 'message': "Product Remove From Favorite"})

    return JsonResponse({'status': True, 'message': "Product Already Removed From Favorite"})


@login_required(login_url='web_login')
def active_favorite_product(request):
    user_id = request.user.id
    favorite_product = Favorite.objects.filter(user_id=user_id)
    serializer = FavoriteProductSerializer(favorite_product, many=True)
    return JsonResponse({'success': True, 'payload': serializer.data})


@login_required(login_url='web_login')
def delete_favorite(request, id):
    user_id = request.user.id
    Favorite.objects.filter(user_id=user_id, imagine_id=id).delete()
    messages.success(request, "Product Removed From Favorite")
    return redirect('view_favorites')


@login_required(login_url='web_login')
def view_favorites(request):
    user_id = request.user.id
    favorites = Favorite.objects.filter(user_id=user_id, imagine__is_delete=False)

    imagine_id_list = []

    for i in favorites:
        imagine_id_list.append(i.imagine_id)

    imagine_product_imgs = ImagineProductImage.objects.filter(imagine_product_id__in=imagine_id_list)
    imagine_subtable_imgs = ImagineProductImageSubTable.objects.all()

    return render(request, 'pages/my-account/my-account-favorites.html', {'favorites': favorites, 'imagine_product_imgs': imagine_product_imgs, 'imagine_subtable_imgs': imagine_subtable_imgs})

@login_required(login_url='web_login')
def my_account_order_detail(request, slug):
    product_order = ProductOrder.objects.get(order_id = slug)
    product_order_id = product_order.id 
    product_order_data = ProductOrderData.objects.filter(product_order_id=product_order_id)
    product_in_order_count = product_order_data.count()
    product_image = ShopProductImage.objects.all()   
    original_price = []
    offer_price = []
    quantity = []
    for order in product_order_data:
        count = order.quantity
        quantity.append(count)
        original = float(order.shop_product.original_price * order.quantity)
        original_price.append(original)
        offer = float(order.per_unit_price * order.quantity)
        offer_price.append(offer)

    product_original_price =sum(original_price)
    product_offer_price = sum(offer_price)
    total_quantity = sum(quantity)
    if product_order.offer_id:
        offer_data = Offer.objects.get(id = product_order.offer_id)
        price_after_offer = (product_offer_price * offer_data.percentage)/100
        total_savings = product_original_price - price_after_offer
    else:
        offer_data = None
        total_savings = product_original_price - product_offer_price
        price_after_offer = None

    data = {
        'price_after_offer': price_after_offer,
        'offer_data': offer_data,
        'product_in_order_count': product_in_order_count,
        'product_order_data': product_order_data,
        'product_image': product_image,
        'product_order': product_order,
        'product_original_price': product_original_price,
        'product_offer_price': product_offer_price,
        'total_quantity': total_quantity,
        'total_savings': total_savings   
    }
    return render(request, 'pages/my-account/my-account-order-detail.html', data)


@login_required(login_url='web_login')
def my_account_order(request):
    user_id = request.user.id
    product_order = ProductOrder.objects.filter(user_id=user_id).order_by('-id')
    p = Paginator(product_order, per_page=3)
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number)  # returns the desired page object
    except PageNotAnInteger:
        # if page_number is not an integer then assign the first page
        page_obj = p.page(1)
    except EmptyPage:
        # if page is empty then return last page
        page_obj = p.page(p.num_pages)


    cancelable_order_id = []
    for order in product_order:
        time = order.order_at
        remaining_time = (datetime.now() - time).total_seconds()
        if remaining_time <= float(86400):
            cancelable_order_id.append(order.id)      
    
    order_ids = []
    for order in product_order:
        order_ids.append(order.id)

    product_order_data = ProductOrderData.objects.filter(product_order_id__in=order_ids).order_by('-id')

    product_ids = []
    for product in product_order_data:
        product_ids.append(product.shop_product_id)

    shop_product_image = ShopProductImage.objects.filter(shop_product_id__in=product_ids)

    data = {
        'page_obj': page_obj,
        'cancelable_order_id': cancelable_order_id,
        'product_orders': product_order,
        'product_order_data': product_order_data,
        'shop_product_images': shop_product_image
    }

    return render(request, 'pages/my-account/my-account-order.html', data)


def cancel_user_order(request):
    # try:
        id = request.POST.get("order_id")
        orders_data = ProductOrder.objects.get(id = id)
        product_data = ProductOrderData.objects.filter(product_order_id = id)
        for product in product_data:
            order_product_id = product.shop_product_id
            shop_product = ShopProduct.objects.get(id = order_product_id)
            shop_product.quantity += product.quantity
            shop_product.save()
        order_at = orders_data.order_at
        current_time = datetime.now()
        remaining_time = (current_time - order_at).total_seconds() / 3600.0
        order_id = orders_data.order_id

        if remaining_time <= float(24):
            delete_order(orders_data.order_id)
            amount_refunded = cancel_order_refund(request, orders_data)
            if not amount_refunded['status']:
                messages.error(request, amount_refunded['message'])
                return redirect('my_account_order')
            try:
                cancel_order_sms(request.user.name, request.user.country_code,request.user.mobile, orders_data.total_amount, order_id)
            except:
                pass
            email = request.user.email
            name = request.user.name
            try:
                cancel_order(email, name, order_id)
            except:
                pass        
            messages.success(request, amount_refunded['message'])
            return redirect("my_account_order")
    # except:
        # messages.error(request, "Something Went Wrong")
        # return redirect("my_account_order") 
    


# to show user's active shero subscription plan and other available shero subscription paln
@login_required(login_url='web_login')
def my_account_subscription(request):
    try:
        id = request.user.id
        user_subscription = UserSubscriptions.objects.filter(user_id = id)
        if bool(user_subscription):
            user_subscription = user_subscription.first()

        subscription_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
        subscriptions = SubscriptionPlanAndBenefits.objects.all()
        if request.user.is_authenticated:
            shero_subscription_expire(id)
        return render(request, 'pages/my-account/my-account-subscription.html', {'user_subscription': user_subscription, 'subscriptions': subscriptions, 'subscription_plans': subscription_plans})
    except Exception as err:
        messages.error(request, "Something Went Wrong")
        return redirect('home')

@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        try:
            # token_and_secret_key = TokenAndSecretKey.objects.get(name="STRIPE_PUBLIC_KEY")
            stripe_config = {"publicKey": settings.STRIPE_PUBLIC_KEY}
            return JsonResponse(stripe_config, safe=True)
        except:
            return JsonResponse({"publicKey": None}, safe=True)

# to subscribe to shero dolls subscription
@csrf_exempt
# @login_required(login_url='web_login')
def shero_subscribe(request):
    try:
        if request.user.is_anonymous:
            return JsonResponse({'success': False, 'message': 'Sign In or Create an Account'})
        
        if request.method == "POST":
            data_dict = json.loads(request.body)
            slug = data_dict.get('slug')
            user_id = request.user.id
            
            if UserSubscriptions.objects.filter(user_id=user_id, shero_subscription_id__isnull=False).exists():
                return JsonResponse({'success': False, 'message': 'You Already have Active Subscription Plan. To Buy Other Plan Please Cancel Previous Subscription First'})

            if not UserSubscriptions.objects.filter(user_id=user_id).exists():
                customer = create_customer(request.user.email.lower())

                user_subscription = UserSubscriptions()
                user_subscription.user_id = user_id
                user_subscription.customer_id = customer.id
                user_subscription.save()
            
            user_subscription = UserSubscriptions.objects.get(user_id = user_id)
            subscription_plan = SubscriptionPlan.objects.get(slug=slug)
            customer_id = user_subscription.customer_id
            
            subscription_price_id = subscription_plan.subscription_price_id
            line_items = [
                {
                    "price": subscription_price_id,
                    "quantity": 1,
                }
            ]
            subscription_payment = payment_for_subscription(line_items=line_items, success_url='success_shero_subscription/', cancel_url='subscription', user_id = user_id, customer_id=customer_id)
            request.session['subscription_data'] = {
                'checkout_session_id': subscription_payment['id'],
                'shero_subscription_slug': slug
            }
            request.session.modified = True
            return JsonResponse({'sessionId': subscription_payment['id']})
    except Exception as err:
        return JsonResponse({'success': False, 'message': 'Something Went Wrong'})

def success_shero_subscription(request):
    subscription_data = request.session['subscription_data']
    del request.session['subscription_data']
    request.session.modified = True
    checkout_session = retrive_checkout_session(subscription_data.get('checkout_session_id'))
    if checkout_session.status == 'complete':
        subscription_obj = get_subscription(checkout_session.subscription)
        start_at = subscription_obj.current_period_start
        end_at = subscription_obj.current_period_end
        shero_subscription_slug = subscription_data.get('shero_subscription_slug')
        shero_subscription_plan = SubscriptionPlan.objects.filter(slug=shero_subscription_slug).first()
      
        user_subscription = UserSubscriptions.objects.get(user_id=request.user.id)
        user_subscription.shero_subscription_id = shero_subscription_plan.id
        user_subscription.subscription_id = checkout_session.subscription
        user_subscription.start_at = datetime.fromtimestamp(start_at).strftime('%Y-%m-%d')
        user_subscription.expire_at = datetime.fromtimestamp(end_at).strftime('%Y-%m-%d')
        user_subscription.save()
        if user_subscription.shero_subscription.offer_price > 0:
            subscription_price = user_subscription.shero_subscription.offer_price
        else:
            subscription_price = user_subscription.shero_subscription.original_price
        messages.success(request, "Thank You For Subscribing")
        name = user_subscription.user.name
        email = user_subscription.user.email.lower()
        UserSubscriberHistory.objects.create(   user_id = user_subscription.user_id, 
                                                plan_type = user_subscription.shero_subscription.plan_type, 
                                                subscription_id = user_subscription.subscription_id,
                                                price = subscription_price,
                                                start_at = user_subscription.start_at,
                                                expire_at = user_subscription.expire_at,
                                                status = True   )
        try:
            shero_dolls_subscription_confirmation(email, name)    
        except:
            pass
        try:
            shero_subscription_plan_activation(request.user.name, request.user.country_code,request.user.mobile)
            # subscription_payment_confirmations_sms(request.user.name, request.user.country_code,request.user.mobile)
        except:
            pass
    else:
        messages.success(request, "Failed Get Subscription")
        
    return redirect('my_account_subscription')

def redeem_shero_subscription(request):
    if request.user.is_anonymous:
        return JsonResponse({'success': False, 'message': 'Sign In or Create an Account'})
    
    if request.method == "POST":
        otp = request.POST.get('redeem_otp')
        gift_code = request.POST.get('gift_code')
        if request.user.otp != otp:
            messages.error(request, "Wrong OTP")
            return redirect('redeem_my_gift_card')
        elif UserSubscriptions.objects.filter(user_id=request.user.id, shero_subscription_id__isnull=False).exists():
            plan_type = UserSubscriptions.objects.get(user_id=request.user.id, shero_subscription_id__isnull=False).shero_subscription.plan_type
            messages.error(request, f'{plan_type} Subscription is Already Active')
            return redirect('redeem_my_gift_card')
        elif not UserGiftCard.objects.filter(receiver_email=request.user.email.lower()).exists():
            messages.error(request, "No Gift Card Available")
            return redirect('redeem_my_gift_card')

        user_gift_card = UserGiftCard.objects.get(gift_code=gift_code, gift_card_type="SHERO_SUBSCRIPTION_GIFT_CARD")
        user_gift_card.is_used = True
        user_gift_card.used_at = datetime.now()
        user_gift_card.save()

        subscription_months = interval_dict.get(user_gift_card.subscription_plan.plan_type)
        user_subscription = UserSubscriptions.objects.get(user_id=request.user.id)
        user_subscription.shero_subscription_id = user_gift_card.subscription_plan_id

        start_at = datetime.now().strftime('%Y-%m-%d')
        expire_at = parse(start_at) + relativedelta(months=subscription_months) 

        user_subscription.start_at = start_at
        user_subscription.expire_at = expire_at
        user_subscription.save()
        
        messages.success(request, "Thank You For Subscribing")
        name = user_subscription.user.name
        email = user_subscription.user.email.lower()
        shero_dolls_subscription_confirmation(email, name)    
        try:
            shero_subscription_plan_activation(request.user.name, request.user.country_code,request.user.mobile)
        except:
            pass
        messages.success(request, "Shero Subscription Gift Card Redeemed and Subscription Activated Successfully")
        return redirect('my_account_subscription')

def shero_subscription_expire(user_id):
    if UserSubscriptions.objects.filter(user_id=user_id).exists():
        user_subscription = UserSubscriptions.objects.get(user_id=user_id)
        today_date = datetime.now().date()
        expire_at = user_subscription.expire_at
        if expire_at and today_date > expire_at:
            user_subscription.subscription_id = None
            user_subscription.shero_subscription_id = None
            user_subscription.start_at = None
            user_subscription.expire_at = None
            user_subscription.save()


def cancel_shero_subscription(request):
    user_id = request.user.id
    user_subscription = UserSubscriptions.objects.filter(user_id=user_id)
    time = timezone.now()
    if user_subscription.exists():
        user_subscription = user_subscription.first()
        if user_subscription.subscription_id:
            cancel_stripe_subscription(user_subscription.subscription_id)
            user_subscription_history = UserSubscriberHistory.objects.get(subscription_id = user_subscription.subscription_id)
            user_subscription_history.canceled = True
            user_subscription_history.canceled_at = time
            user_subscription_history.save()
        user_subscription.subscription_id = None
        user_subscription.shero_subscription_id = None
        user_subscription.start_at = None
        user_subscription.expire_at = None
        user_subscription.save()
        try:
            cancel_subscription_sms(request.user.name, request.user.country_code, request.user.mobile)
        except:
            pass
        try:
            send_mail_subscription_cancel(request.user.email.lower(), request.user.name)
        except:
            pass
        messages.success(request, 'Shero Doll Subscription Has Been Cancel')
    else:
        messages.error(request, 'You Do not Have Shero Doll Subscription Please Purchase It')
    
    return redirect('my_account_subscription')

# to cancel shero dolls subscription plan from my subscriptions
def cancel_subscription(request):
    try:
        id = request.POST.get("cancel_subscription")
        UserSubscriptions.objects.get(id=id).delete()
        messages.success(request, "Subscription Deleted")
        return redirect("my_account_subscription")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect(request.META.get('HTTP_REFERER'))


# to show shero dolls subscription page
def subscription(request):
    try:
        user_subscription = None
        if request.user.is_authenticated:
            id = request.user.id
            shero_subscription_expire(id)

            user_subscription = UserSubscriptions.objects.filter(user_id = id)
            if bool(user_subscription):
                user_subscription = user_subscription.first()

        subscription_content_data = SheroSubscriptionContent.objects.get(id = 1)
        subscription_plan = SubscriptionPlan.objects.filter(is_active = True).order_by('sort_order')
        subscription_benefits = SubscriptionPlanAndBenefits.objects.all()
        shero_dolls = SheroDollsImage.objects.filter(shero_dolls__is_active = True)
        shero_dolls_image = SheroDollsImageSubTable.objects.all()
        return render(request, 'pages/subscription.html', {"subscription_content_data": subscription_content_data, "shero_dolls": shero_dolls, "shero_dolls_image": shero_dolls_image, "subscription_plan": subscription_plan, "subscription_benefits": subscription_benefits, 'user_subscription': user_subscription, 'site_url': settings.SITE_URL})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('home')


# to show details of shero dolls from where user can add it to cart or buy
# @login_required(login_url='web_login') 
def buy_shero_dolls(request, slug):
    try:
        user_id = request.user.id
        # user_subscription_data = UserSubscriptions.objects.get(user_id = user_id)
        # if user_subscription_data.subscription_id:
        id = SheroDolls.objects.get(slug=slug).id
        limited_print_year = int(SheroDolls.objects.get(slug=slug).year)+1
        cart_obj = get_cart_obj(request)
        cart_item = False
        if cart_obj:
            shero_dolls_list = string_to_list(cart_obj.shero_dolls_list)
            if id in shero_dolls_list:
                cart_item = True

        shero_dolls = SheroDollsImage.objects.get(shero_dolls_id = id)
        shero_dolls_image = SheroDollsImageSubTable.objects.filter(shero_dolls_image_id = id)
        return render(request, 'pages/previous-shero.html', {"shero_dolls": shero_dolls, "limited_print_year":limited_print_year,
            "shero_dolls_image": shero_dolls_image, 'site_url': settings.SITE_URL, 'cart_item': cart_item})
        # else:
        #     messages.error(request, "Please Buy Subscription Plan First to Buy Shero Dolls")
        #     return redirect('subscription')
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription')


@login_required(login_url='web_login')
def my_account_wallet(request):
    return render(request, 'pages/my-account/my-account-wallet.html')

@login_required(login_url='web_login')
def my_account_referrals(request):
    id = request.user.id
    user = User.objects.get(id = id)
    try:
        if not user.referral_code:
            name = user.name.replace(" ", "").upper()
            digits = random_with_N_digits(8)
            new_referral_code = f"{name}{digits}"
            user.referral_code = new_referral_code
            user.save()
    except:
        pass
    code = user.referral_code
    link = f"{settings.SITE_URL}referral_sign_up/{user.referral_code}"
    referrals = UserReferral.objects.filter(user_from_id = id)
    referral_content_data = ReferralContent.objects.get(id = 1) 
    total_points = UserReferral.objects.filter(order_status = True).count()
    total_points = total_points // 3
    received_dolls = user.dolls_got_count
    dolls_to_recieve = user.dolls_to_get_count
    points = total_points - received_dolls
    return render(request, 'pages/my-account/my-account-referrals.html', 
                            {"referral_content_data": referral_content_data,
                            "link": link, "total_points": total_points,
                            "dolls_to_recieve": dolls_to_recieve,
                            "received_dolls": received_dolls,
                            "referral_code": code,
                            "referrals": referrals,
                            'points': points})

# @login_required(login_url='web_login')
@csrf_exempt
def my_account_wishlist(request):
    id = request.user.id
    if request.user.is_authenticated:
        if request.method == 'POST':
            product_id = request.POST.get('id')
            user_id = request.user.id
            # 1 = shop, 2 = imagine
            is_added = False

            if Wishlist.objects.filter(user_id=user_id, shop_id=product_id).exists():
                Wishlist.objects.filter(user_id=user_id, shop_id=product_id).delete()
                msg = "Product Removed from Wishlist"
            else:
                Wishlist.objects.create(user_id=user_id, shop_id=product_id)
                msg = "Product Added to Wishlist"
                is_added = True

            return JsonResponse({'status':True, 'is_added': is_added, 'message': msg})
    else:
        return JsonResponse({'status': False, 'message': "You need to login first"})


@login_required(login_url='web_login')
def active_wishlist_product(request):
    user_id = request.user.id
    wishlist_product = Wishlist.objects.filter(user_id=user_id)
    serializer = WishlistProductSerializer(wishlist_product, many=True)
    return JsonResponse({'success': True, 'payload': serializer.data})



@login_required(login_url='web_login')
def add_to_wishlish_cart(request, id):
    try:
        if request.user.is_authenticated:
            user_id = request.user.id
            if not Wishlist.objects.filter(user_id=user_id, shop_id=id).exists():
                Wishlist.objects.create(user_id=user_id, shop_id=id)
                messages.success(request, 'Added to Wishlist')
            else:
                messages.success(request, 'Product Already in Wishlist')
        else:
            messages.error(request, 'Please Login First')
    except:
        messages.error(request, 'Failed to add to Wishlist')
    return redirect('view_cart')


@login_required(login_url='web_login')
def add_to_wishlish_doll_detail(request, slug):
    if request.user.is_anonymous:
        messages.error(request, 'Please Login First')
        return redirect('shop_doll_detail', slug)

    try:
        id = get_shop_product_id(slug)
        user_id = request.user.id
        if not Wishlist.objects.filter(user_id=user_id, shop_id=id).exists():
            Wishlist.objects.create(user_id=user_id, shop_id=id)
            messages.success(request, "Product Added to Wishlist")
    except:
        messages.error(request, "Something Went Wrong")
    return redirect('shop_doll_detail', slug)


@login_required(login_url='web_login')
def remove_from_wishlish_doll_detail(request, slug):
    if request.user.is_anonymous:
        messages.error(request, 'Please Login First')
        return redirect('shop_doll_detail', slug)

    try:
        id = get_shop_product_id(slug)
        wishlist_product = Wishlist.objects.filter(user_id=request.user.id, shop_id=id)
        if wishlist_product.exists():
            wishlist_product.delete()
            messages.success(request, 'Product Remove from Wishlist')
    except:
        messages.error(request, 'Something Went Wrong')
    return redirect('shop_doll_detail', slug)



@login_required(login_url='web_login')
def view_wishlist(request):
    user_id = request.user.id
    wishlist = Wishlist.objects.filter(user_id=user_id, shop__is_delete=False)
    
    shop_id_list = []
    imagine_id_list = []

    for i in wishlist:
        if i.shop_id:
            shop_id_list.append(i.shop_id)
        else:
            imagine_id_list.append(i.imagine_id)

    shop_product_imgs = ShopProductImage.objects.filter(shop_product_id__in = shop_id_list)
    shop_subtable_imgs = ShopProductImageSubTable.objects.all()
    cart_obj = get_cart_obj(request)
    cart_product_list = []
    if cart_obj:
        cart_product_list = string_to_list(cart_obj.shop_product_list)

    imagine_product_imgs = ImagineProductImage.objects.filter(imagine_product_id__in = imagine_id_list)
    imagine_subtable_imgs = ImagineProductImageSubTable.objects.all()

    return render(request, 'pages/my-account/my-account-wishlist.html', {'wishlist': wishlist, 'shop_product_imgs': shop_product_imgs, 'shop_subtable_imgs': shop_subtable_imgs, 'imagine_product_imgs': imagine_product_imgs, 'imagine_subtable_imgs': imagine_subtable_imgs, 'cart_product_list': cart_product_list})



@login_required(login_url='web_login')
def order_confirmation(request):
    return render(request, 'pages/order-confirmation.html')


# @login_required(login_url='web_login')
def payment(request):
    if request.META.get('HTTP_REFERER') == None or not reverse('billing') in request.META.get('HTTP_REFERER'):
        return redirect('billing')
    
    sub_total = request.session['order_data'].get('sub_total')
    shipment_cost = request.session['order_data'].get('shipment_cost')
    # tax = request.session['order_data'].get('tax')
    sub_total_with_shipping = request.session['order_data'].get('sub_total_with_shipping')
    wallet_amount = request.user.wallet

    return render(request, 'pages/payment.html', {'STRIPE_PUB_KEY': settings.STRIPE_PUBLIC_KEY, 'sub_total': sub_total, 'shipment_cost': shipment_cost, 'sub_total_with_shipping': sub_total_with_shipping, 'wallet_amount': wallet_amount})



# User Profile Start
# to show user profile details
@login_required(login_url='web_login')
def profile(request):
    try:
        id = request.user.id
        user_data = User.objects.get(id=id)
        try:
            Profile.objects.get(user_id = id)
        except:
            Profile.objects.create(user_id = id)
        user_bio_data = Profile.objects.get(user_id = id)                     
        return render(request, 'pages/profile/profile.html', {'user': user_data, 'bio': user_bio_data})
    except:
        messages.error(request,"Something Went Wrong")
        return redirect('/')

# to edit user's details from my profile 
@login_required(login_url='web_login')
@csrf_exempt
def profile_edit(request ):
    try:
        id = request.user.id  
        user_data = User.objects.get(id=id)
        bio_data = Profile.objects.get(user_id=id)
        bio = bio_data.bio
        if request.method == "POST":
            new_name = request.POST.get('user_name')
            birthday = request.POST.get('birthday')
            new_img = request.FILES.get('user_img')
            country_code = request.POST.get("country_code")
            new_mobile = request.POST.get('mobile')
            new_bio = request.POST.get('user_bio')
            if len(new_bio) > 255:
                messages.error(request, "Bio Character Limit is 255")
                return render(request, 'pages/profile/profile-edit.html', {'user': user_data, 'bio': new_bio, 'bio_data': bio_data})
            if new_img:
                user_data.profile_img = new_img
            if birthday:
                try:
                    bio_data.birthday = birthday
                except:
                    messages.error(request, "Data format should be DD-MM-YYYY")      
                    return redirect('web_profile_edit')
            user_data.name = new_name
            user_data.save()   
            bio_data.bio = new_bio
            bio_data.save()
            if new_mobile: 
                if User.objects.filter(country_code=country_code, mobile=new_mobile, is_delete=False).exists():
                    messages.error(request, "Number Already Exist")
                    return redirect("web_profile_edit")
                else:    
                    otp = random.randint(100000, 999999)
                    user_data.otp = otp
                    user_data.save()
                    try:
                        update_mobile(user_data.name, otp, country_code, new_mobile) # this function is in twilio.py and used to send mobile messgaes
                        messages.success(request, "Verification OTP Sent to Your New Number")
                        return redirect('mobile_update', country_code, new_mobile) 
                    except Exception as e:
                        print(e, "-=-=-=-=-===")
                        messages.error(request, "Invalid Number")      
                        return redirect ('web_profile_edit')
                   
            else:
                messages.success(request, 'Profile Updated')    
                return redirect('web_profile')
        return render(request, 'pages/profile/profile-edit.html', {'user': user_data, 'bio': bio, 'bio_data': bio_data})
    except:
        messages.error(request,"Something Went Wrong")  
        return redirect('web_profile')    
    


# to update mobile number from my profile
def mobile_update(request, country_code, new_mobile):
    id = request.user.id
    user_data = User.objects.get(id=id)
    otp = request.POST.get('otp')
    if otp:
        if otp == user_data.otp:
            user_data.mobile = new_mobile
            user_data.country_code = country_code 
            user_data.save()  
            messages.success(request, "Mobile Number Updated") 
            return redirect('web_profile')
        else:
            messages.error(request, "Wrong OTP")
            return render(request, 'pages/profile/mobile_edit.html', {"country_code": country_code, "new_mobile": new_mobile})
    return render(request, 'pages/profile/mobile_edit.html', {"country_code": country_code,   "new_mobile": new_mobile})

# to resend otp to mobile 
def resend_otp_mobile(request, country_code, new_mobile):
    id = request.user.id
    user_data = User.objects.get(id=id)
    otp = random.randint(100000, 999999)
    user_data.otp = otp
    user_data.save()
    try:
        update_mobile(user_data.name, otp, country_code, new_mobile) # this function is in twilio.py and used to send messgaes to mobile 
        messages.success(request, "Verification OTP Sent to Your New Number")
        return redirect('mobile_update',country_code, new_mobile) 
    except:
        messages.error(request, "Message Not Sent")      
        return redirect ('web_profile_edit')
# User Profile End


@login_required(login_url='web_login')
def stripe_checkout(request):
    # try:
    #     token_and_secret_key = TokenAndSecretKey.objects.get(name="STRIPE_PUBLIC_KEY")
    #     return render(request, 'pages/payment/stripe-checkout.html', {'STRIPE_PUB_KEY': token_and_secret_key.key})
    # except:
    return render(request, 'pages/payment/stripe-checkout.html', {'STRIPE_PUB_KEY': settings.STRIPE_PUBLIC_KEY})

def products_data(request):
    total_amount = 0
    total_quantity = 0
    try:
        cart = UserCart.objects.get(user_id=request.user.id)
        product_list = string_to_list(cart.shop_product_list)
        product_dict = dict(Counter(product_list))
        product_data = ShopProduct.objects.filter(id__in=product_list)

        for data in product_data:
            doll_quantity = product_dict.get(data.id)
            doll_price = 0

            if data.offer_price > 0:
                doll_price = data.offer_price
            else:
                doll_price = data.original_price

            total_quantity += doll_quantity
            total_amount += doll_quantity * doll_price
            
        return {'success': True, 'total_amount': total_amount, 'total_quantity': total_quantity}
    except:
        return {'success': False, 'total_amount': total_amount, 'total_quantity': total_quantity}
        

@login_required(login_url='web_login')
def create_checkout_session(request):
    if request.method == 'POST':
        # request.session['product_order_id'] = product_order_id
        # request.session.modified = True
        data_dict = json.loads(request.body)
        is_walled_selected = data_dict.get('is_walled_selected')
        sub_total_with_shipping = float(request.session['order_data'].get('sub_total_with_shipping'))
        remaining_pay_amount = sub_total_with_shipping
        if request.session.has_key('remaining_wallet_balance'):
            del request.session['remaining_wallet_balance']
        if request.session.has_key('remaining_pay_amount'):
            del request.session['remaining_pay_amount']
        if request.session.has_key('payment_intent_id'):
            del request.session['payment_intent_id']
        request.session.modified = True
        
        if is_walled_selected:
            wallet_balance = float(request.user.wallet)
            if wallet_balance >= sub_total_with_shipping:
                request.session['remaining_wallet_balance'] = wallet_balance - sub_total_with_shipping
                request.session.modified = True
                return JsonResponse({'success': True, 'is_wallet': True})
            else:
                remaining_pay_amount = sub_total_with_shipping - wallet_balance
                request.session['remaining_pay_amount'] = remaining_pay_amount
                request.session.modified = True
        
        try:
            total_data = products_data(request)
            domain = settings.SITE_URL
            # Set Stripe API key
            stripe.api_key = settings.STRIPE_SECRET_KEY
            user_subscrption = UserSubscriptions.objects.filter(user_id=request.user.id)
            customer_id = None
            if user_subscrption:
                customer_id = user_subscrption[0].customer_id
        
            order_data =  request.session['order_data']
            # billing_address_id = order_data.get('billing_address_id')
            # billing_address = UserAddress.objects.get(id=billing_address_id)

            shipping_address_id = order_data.get('shipping_address_id')
            shipping_address = UserAddress.objects.get(id=shipping_address_id)
            # tax_rate = stripe.TaxRate.create(
            #     display_name="VAT",
            #     description="VAT ",
            #     jurisdiction="DE",
            #     percentage=16,
            #     country="US",
            #     state="NY",
            #     inclusive=True,
            # )


            stripe.Customer.modify(
                customer_id,
                # address={
                #     'line1': billing_address.area_name,
                #     # 'line2': billing_address['line2'],
                #     'city': billing_address.web_city,
                #     'state': billing_address.web_state.name,
                #     'country': billing_address.web_country.short_name,
                #     'postal_code': billing_address.zip_code,
                # },
                shipping={
                    'address': {
                        'line1': shipping_address.area_name,
                        # 'line2': shipping_address['line2'],
                        'city': shipping_address.web_city,
                        'state': shipping_address.web_state.name,
                        'country': shipping_address.web_country.short_name,
                        'postal_code': shipping_address.zip_code,
                    },
                    'name': shipping_address.user.name
                }
            )

            # address={
            #         'line1': shipping_address.area_name,
            #         # 'line2': shipping_address['line2'],
            #         'city': shipping_address.web_city,
            #         'state': shipping_address.web_state.name,
            #         'country': shipping_address.web_country.short_name,
            #         'postal_code': shipping_address.zip_code,
            #     },
                # shipping={
                #     'address': {
                #         'line1': shipping_address.area_name,
                #         # 'line2': shipping_address['line2'],
                #         'city': shipping_address.web_city,
                #         'state': shipping_address.web_state.name,
                #         'country': shipping_address.web_country.short_name,
                #         'postal_code': shipping_address.zip_code,
                #     },
                #     'name': shipping_address.user.name
                # }


            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                mode = 'payment',
                success_url = domain + f"success/",
                cancel_url = domain + "cancelled/",
                line_items = [{
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(remaining_pay_amount * 100),
                        "tax_behavior": "exclusive",
                        "product_data": {
                            "name": "total quantity of Product " + str(total_data.get('total_quantity')),
                            "tax_code": STRIPE_TAX_CODE['product'],
                        }
                    },
                    # "tax_rates": ['txr_1MokNCEoxvNu9SZpSVDJR6BQ']
                }],
                automatic_tax={
                    'enabled': True,
                },
                billing_address_collection="required",
                shipping_address_collection={
                    "allowed_countries": ["US"],
                },
                customer_update={
                    # 'address': 'auto',
                    'shipping': 'auto'
                },
            )

            # line_items=[
                #     {
                #         'name': "total quantity of Product " + str(total_data.get('total_quantity')),
                #         'currency': 'usd',
                #         'amount': int(remaining_pay_amount * 100),
                #         'quantity': 1,
                #     },
                # ],

            
            request.session['session_id'] = checkout_session.id
            request.session['payment_intent_id'] = checkout_session.payment_intent
            request.session.modified = True
            return JsonResponse({'sessionId': checkout_session['id']})

        except stripe.error.CardError as e:
            return JsonResponse({'message': e.user_message})
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            return JsonResponse({'message': 'Too many requests, please try again after sometimes'})
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            return JsonResponse({'message': 'Invalid Request'})
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            return JsonResponse({'message': 'Something Went Wrong'})
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            return JsonResponse({'message': 'Failed to Connect with Stripe'})
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            return JsonResponse({'message': 'Transaction Failed, Please Try Again'})
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            return JsonResponse({'message': 'Something Went Wrong'})

# to generate a random order id
from random import randint
def generate_order_id(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


@login_required(login_url='web_login')
def stripe_success(request):
    try:
        try:
            check_all_quantity(request)
        except Exception as err:
            messages.error(request, err)
            return redirect('view_cart')
        
        order_data =  request.session['order_data']
        tax = 0
        shipment_cost = order_data.get('shipment_cost')
        sub_total = order_data.get('sub_total')
        sub_total_with_shipping = order_data.get('sub_total_with_shipping')
        # carrier_code = order_data.get('carrier_code')
        carrier_service_name = order_data.get('carrier_service_name')
        shipping_address_id = order_data.get('shipping_address_id')
        billing_address_id = order_data.get('billing_address_id')
        
        shipping_address = UserAddress.objects.get(id=shipping_address_id)
        billing_address = UserAddress.objects.get(id=billing_address_id)
        
        data = None 
        product_order = None
        product_data = None
        user_id = request.user.id
        intent = None
        
        # checking if cart has any item
        '''
            this [if] and [else] rendering data if cart object exists then 
            use that data or else fetch data from ProductOrder and ProductOrderData model 
        '''
        if UserCart.objects.filter(user_id=user_id).exists():
            # this variable to check if we need to run more or stop there
            further_proceed_status = False
            has_remaining_wallet_balance = request.session.has_key('remaining_wallet_balance') 
            has_remaining_pay_amount = request.session.has_key('remaining_pay_amount')
            has_payment_intent_id = request.session.has_key('payment_intent_id')
            # this if elif is because to check if user paid amount or not
            # here checking if user paying full amount from stripe
            if has_payment_intent_id:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                payment_intent_id = request.session.get('payment_intent_id', None)
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                checkout_session = retrive_checkout_session(request.session.get('session_id'))
                tax = (checkout_session.total_details.amount_tax / 100)
                del request.session['payment_intent_id']
                request.session.modified = True
                further_proceed_status = intent.status == 'succeeded'
            elif has_remaining_wallet_balance: # else user paying from wallet
                further_proceed_status = True
                
            if further_proceed_status:
                cart = UserCart.objects.get(user_id=user_id)
                UserCart.objects.filter(user_id = user_id).delete()
    
                product_list = string_to_list(cart.shop_product_list)
                product_dict = dict(Counter(product_list))
                product_data = ShopProduct.objects.filter(id__in=product_list)
                order_id = generate_order_id(10)
                
                # substracting product quantity from available stock which user buy 
                for product in product_data:
                    product.available_quantity -= product_dict.get(product.id)
                    product.save()
                
                # if generated order id already exist in table then we generate a new order id
                while ProductOrder.objects.filter(order_id=order_id).exists():
                    order_id = generate_order_id(10)
                total_amount = (sub_total_with_shipping + tax)
                product_order = ProductOrder()
                product_order.tax = tax
                product_order.shipping_charge = shipment_cost
                product_order.total_amount = total_amount

                if intent:
                    product_order.card_brand = intent.charges.data[0].payment_method_details.card.brand
                    
                product_order.carrier_service_name = carrier_service_name
                product_order.user_id = user_id
                product_order.order_id = order_id
                product_order.shipping_address_id = shipping_address_id
                product_order.billing_address_id = billing_address_id

                if cart.offer_id:
                    product_order.offer_id = cart.offer_id
                    
                amount_dict = {}
                # this condition checking if one of those key exist in session that means user pay from wallet 
                if has_remaining_pay_amount or has_remaining_wallet_balance:
                    if has_remaining_pay_amount:
                        amount_to_pay = request.session['remaining_pay_amount'] + tax
                        pay_from_wallet = request.user.wallet
                        amount_dict = {
                            'stripe': amount_to_pay,
                            'wallet': pay_from_wallet
                        }
                        product_order.paid_by_stripe = amount_to_pay
                        product_order.paid_by_wallet = pay_from_wallet
                        del request.session['remaining_pay_amount']
                    elif has_remaining_wallet_balance:
                        amount_dict['wallet'] = product_order.paid_by_wallet = sub_total_with_shipping
                        del request.session['remaining_wallet_balance']
                    request.user.wallet = float(request.user.wallet) - float(product_order.paid_by_wallet)
                    request.user.save()
                    
                    wallet_transacton = WalletTransaction()
                    wallet_transacton.user_id = user_id
                    wallet_transacton.amount = product_order.paid_by_wallet
                    wallet_transacton.remaining_wallet_balance = request.user.wallet
                    wallet_transacton.amount_status = 'WITHDRAW'
                    wallet_transacton.transaction_type = 'PAYMENT'
                    wallet_transacton.save()
                else:   # or else user paid full amount through stripe
                    amount_dict['stripe'] = product_order.paid_by_stripe = sub_total_with_shipping + tax

                product_order.order_status = "Completed"
                product_order.save()
                product_order.get_delivery_date()

                if cart.offer_id:
                    used_offer = UsedOffer.objects.get(offer_id = cart.offer_id, user_id = user_id)
                    used_offer.is_used = True
                    used_offer.save()
                
                if UserReferral.objects.filter(user_to_id = user_id).exists():
                    user_referral_data = UserReferral.objects.get(user_to_id = user_id)
                    if not user_referral_data.order_id:
                        user_referral_data.order_id = product_order.id
                        user_referral_data.save()
                        
                            
                for data in product_data:
                    doll_price = 0
                    if data.offer_price > 0:
                        doll_price = data.offer_price
                    else:
                        doll_price = data.original_price

                    ProductOrderData.objects.create(
                        quantity = product_dict.get(data.id),
                        per_unit_price = doll_price,
                        product_order_id = product_order.id,
                        shop_product_id = data.id
                    )
                
                    # creating order for ship station api
                    create_order(product_order)
                    

                    user_and_order_backup = UserAndOrderBackup()
                    user_and_order_backup.user_name = request.user.name
                    user_and_order_backup.email = request.user.email.lower()
                    user_and_order_backup.mobile = request.user.mobile
                    user_and_order_backup.order_id = order_id
                    user_and_order_backup.product_name = data.name
                    user_and_order_backup.quantity = product_dict.get(data.id)
                    user_and_order_backup.per_unit_price = doll_price
                    user_and_order_backup.save()
                
                if has_payment_intent_id:
                    OrderDetail.objects.create(
                        user_id = user_id, 
                        product_order_id = product_order.id,
                        stripe_charge_id = intent.charges.data[0].id,
                        balance_transaction = intent.charges.data[0].balance_transaction,
                        amount = intent.charges.data[0].amount / 100,
                        payment_method = intent.charges.data[0].payment_method,
                        reciept_url = intent.charges.data[0].receipt_url,
                        status = intent.charges.data[0].status,
                        payment_intent = intent.charges.data[0].payment_intent,
                        payment_method_types = intent.payment_method_types,
                        customer = intent.customer
                    )
                try:
                    send_mail_order_place(request.user.email.lower(), product_order.order_id, product_order.order_at, amount_dict, request.user.is_authenticated, product_order)
                except:
                    pass 
                try:
                    order_confirmation_sms(request.user.name, request.user.country_code, request.user.mobile, order_id)
                except:
                    pass 
        else:
            product_order = ProductOrder.objects.filter(user_id=user_id).last()
            sub_total = product_order.total_amount - product_order.shipping_charge - product_order.tax
            product_data = ProductOrderData.objects.filter(product_order_id=product_order.id)

        data = {
            'shipping_address': shipping_address,
            'billing_address': billing_address,
            'order_data': product_order,
            'products': product_data,
            'sub_total': round(sub_total, 2)
        }
        
        return render(request, 'pages/order-confirmation.html', data)
    except Exception as err:
        messages.error(request, 'Something Went Wrong')
        return redirect('view_cart')
     


@login_required(login_url='web_login')
def stripe_cancel(request):
    messages.error(request, "Payment Canceled")
    return redirect('view_cart')

# @login_required(login_url='web_login')
@csrf_exempt
def shipping_tax(request):
    try:
        if request.user.is_authenticated:
            services = shipping_station(request)
        else:
            services = guest_user_shipping_station(request, get_cart_obj(request))

        data = json.loads(services.text)
        if 'ExceptionType' in data:
            return JsonResponse({'status': False, 'carrier_services': {}, 'message': 'Please check if zip code is correct or not'}, safe=False)
        else:
            return JsonResponse({'status': True, 'carrier_services': data, 'message': 'Fetched Carrier Services Successfully'}, safe=False)
    except Exception as err:
        return JsonResponse({'status': False, 'carrier_services': {}, 'message': 'Please Try Again After Sometime', 'error': err}, safe=False)


@csrf_exempt
def save_order_data_to_session(request):
    shipping_address_id = request.POST.get('shipping_address')

    shipping_prices = ShippingPrice.objects.all()
    sub_total = float(cart_sub_total(request))
    shipping_price_range = get_shipping_price_range(shipping_prices, sub_total)
    shipping_cost = float(shipping_price_range.shipping_cost)
    sub_total_with_shipping = round(sub_total + shipping_cost, 2)

    request.session['order_data'] = {
        'shipping_address_id': shipping_address_id,
        'billing_address_id': request.POST.get('billing_address'),
        'shipment_cost': shipping_cost,
        'sub_total_with_shipping': sub_total_with_shipping,
        'sub_total': sub_total
    }
    request.session.modified = True
    return JsonResponse({'success': True}, safe=False)

def save_guest_user_cart_data(request):
    cart_data = get_cart_obj(request)
    product_data = []
    if cart_data.shop_product_list:
        shop_product_list = string_to_list(cart_data.shop_product_list)
        shop_products = ShopProduct.objects.filter(id__in=shop_product_list)
        total_amount = 0
        for product in shop_products:
            quantity = shop_product_list.count(product.id)
            price = float(product.offer_price if product.offer_price > 0 else product.original_price)
            amount = quantity * price
            total_amount += amount
            product_data.append({
                'id': product.id,
                'name': product.name,
                'subcategory': product.subcategory.name,
                'quantity': quantity,
                'price': price,
                'amount': amount,
            })
    return product_data


@csrf_exempt
def guest_user_save_order_data_to_session(request):
    order_id = request.session['guest_user']['order_id']
    guest_user_data = GuestUserData.objects.filter(order_id=order_id)
    if guest_user_data:
        guest_user_data = guest_user_data.first()

        product_data = save_guest_user_cart_data(request)
        guest_user_data.order_detail = product_data
        guest_user_data.save()

        shipping_cost = float(guest_user_data.shipping_charge)
        sub_total = round(float(guest_user_data.total_amount) - shipping_cost, 2)
        
        request.session['guest_user']['guest_user_data'] = {
            'shipment_cost': shipping_cost,
            # 'tax': tax,
            'sub_total': sub_total,
            #  + tax
            'total_amount': round(sub_total + shipping_cost, 2),
        }
        request.session.modified = True
        return JsonResponse({'success': True}, safe=False)
    return JsonResponse({'success': False}, safe=False)


# to make user subscribed to blogs 
def blog_subscriber(request):
    try:
        email = request.POST.get("subscriber").lower()
        if BlogSubscriber.objects.filter(email = email).exists():
            messages.success(request, "Already Subscribed")
            return redirect('blog')
        else:    
            data = BlogSubscriber.objects.create(email = email) 
            data.save()
            messages.success(request, "Thank You For Subscribing")
            try:
                blog_subscription_confirmation(email)
            except:
                pass
            return redirect("blog")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("blog") 

        
# subscribing newsletter 
def newsletter(request):
    try:
        if request.method == "POST":
            email = request.POST.get('email').lower()
            if not Newsletters.objects.filter(email = email).exists():
                Newsletters.objects.create(email=email)
                try:
                    newsletter_confirmation(email)
                except:
                    pass
                return JsonResponse({"success": True, "message": "Thank You For Subscribing"})
            else:
                return JsonResponse({"success": True, "message": "Already Subscribed"})
    except:
        return JsonResponse({"success": False, "message": "Something Went Wrong"})

# rating and review on product
def set_product_rating(request):
    if request.method=='POST':
        user_id = request.user.id
        rating=request.POST.get('star')
        product_rating = request.POST.get('product_rating')
        
        product_id = request.POST.get('product_id')
        shop_product = ShopProduct.objects.get(id=product_id)
       
        review = request.POST.get('review')
        if not (product_rating and not product_rating.isspace() and review and not review.isspace()) :
                messages.error(request,'Rating  and  Review Fileds are Required!!!')
                return redirect('shop_doll_detail', shop_product.slug)

        # checking if user already rated and give review on product then update the reviews and rating
        if Review.objects.filter(shopproduct_id=int(product_id)).exists(): 
            set_product_obj=Review.objects.get(user_id=user_id, shopproduct_id=int(product_id))
            set_product_obj.user_id = user_id
            set_product_obj.shopproduct_id = product_id
            set_product_obj.rating=int(product_rating)
            set_product_obj.user_review = review
            set_product_obj.save()
        else:   # else user is giving rating and review to a product first time
           Review.objects.create(shopproduct_id=int(product_id), user_id = user_id, rating=int(product_rating), user_review = review)

        return redirect('shop_doll_detail', shop_product.slug)


# this function show 3 more reviews on a product whenever click on load more button 
@api_view(['GET'])
def load_more_data(request):
    try:
    # object_review=Review.objects.filter(shopproduct_id=id)[:3]
        limt= int(request.GET.get('limit'))
        offset= int(request.GET.get('offset'))
        product= request.GET.get('product_id')

        review_data=Review.objects.filter(shopproduct_id=product)[offset:limt]
        review = {}
        for data in review_data:
            review[data.id] = {
                'username': data.user.name,
                'user_review': data.user_review,
                'rating': data.rating
            }
      
        # load reviews limit set to 3 reviews at a time
        next_records = Review.objects.filter(shopproduct_id=product)[offset+3:limt+3].exists()
        return Response({'success': True, 'payload': review, 'next': next_records})
    except:
        return Response({'success': False, 'payload': {}, 'next': False})


# For the apply coupon:
@csrf_exempt
def apply_offer(request):
    if request.user.is_anonymous:
        return JsonResponse({"succcess": False, "message": "please login first"})

    user_id = request.user.id
    if request.method == 'POST':
        offer_id = request.POST.get('offer_id')
        if not offer_id:
            return JsonResponse({'success': False, 'message': 'Please Select a Coupon'})
        # checking if offer is used
        if UsedOffer.objects.filter(user_id=user_id, offer_id=offer_id, is_used=True).exists():
            return JsonResponse({'success': False, 'message': 'Offer Already Used'})

        # checking if row is in the database table exists if not then create row
        if not UsedOffer.objects.filter(user_id=user_id, offer_id=offer_id, is_used=False).exists():
            UsedOffer.objects.create(user_id=user_id, offer_id=offer_id)

        user_cart = UserCart.objects.get(user_id=user_id)
        user_cart.offer_id = offer_id
        user_cart.save()
        return JsonResponse({"success": True, "message": "Coupon Applied"})

def remove_offer(request):
    user_id = request.user.id
    user_cart = UserCart.objects.get(user_id=user_id)
    user_cart.offer_id = None
    user_cart.save()
    return JsonResponse({"success": True, "message": "Coupon Removed"})


# Generate the gift card  by users and send the another registered users by email:
def create_gift_card(request):
    data = GiftCard.objects.all()
    gift_card_images = GiftCardImage.objects.all()
    giftcard_type = GiftCardType.objects.filter(is_active = True)
    giftcard_type_images = GiftCardTypeImages.objects.all()
    
    subscription_plans = SubscriptionPlan.objects.filter(is_active=True)
    subscription_benefits = SubscriptionPlanAndBenefits.objects.all()

    if request.method=='POST':
        data_dict = json.loads(request.body)

        gift_card_id = data_dict.get('gift_card_id')
        receiver_email = data_dict.get('receiver_email').lower()
        re_enter_receiver_email = data_dict.get('re_enter_receiver_email').lower()
        title = data_dict.get('title')
        message = data_dict.get('message')
        username = data_dict.get('username')
        sender_email_id = data_dict.get("sender_email")
        
        if sender_email_id:
            sender_email = sender_email_id.lower()
        else:
            if request.user.is_authenticated:
                sender_email = request.user.email.lower()
        
        if not sender_email:
            return JsonResponse({'success': False, 'message': 'Your Email is required'})
        elif sender_email == receiver_email:
            return JsonResponse({'success': False, 'message': "Recipient's email and Your email can't be same"})

        giftcard_image_id = data_dict.get("giftcard_image_id")
        
        if not giftcard_image_id:
            return JsonResponse({'success': False, 'message': 'Please Select Gift Card Image'})
        
        if receiver_email != re_enter_receiver_email:
            return JsonResponse({'success': False, 'message': 'Receiver Emails Do Not Match'})
        
        if receiver_email == sender_email or re_enter_receiver_email == sender_email:
            return JsonResponse({'success': False, 'message': 'Receiver Email and Sender Email Cannot be Same'})

        if len(message) > 700:
            return JsonResponse({'success': False, 'message': 'Message Length should be less than or equal to 700 character'})
        
        if not (receiver_email and not receiver_email.isspace() and message and not message.isspace() and title and not title.isspace()):
            return JsonResponse({'success': False, 'message': 'All Fields Are Required!!!'})
        else:
            gift_code = random_with_N_digits(16)
            
            if gift_card_id:
                gift_card = data.get(id=gift_card_id)
                amount = gift_card.gift_price
            else:
                amount = float(data_dict.get('gift_card_amount'))
                if amount <= 0:
                    return JsonResponse({'success': False, 'message': 'Amount Must be greater than 0'})
                
            success_url = 'success_payment_for_gift_card/'
            cancel_url = 'create_gift_card/'
            line_item = [{
                'quantity': 1,
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(amount * 100),
                    'tax_behavior': 'exclusive',
                    'product_data': {
                        'name': 'Gift Card of $' + str(amount),
                        # 'tax_code': STRIPE_TAX_CODE['product'],
                    }
                }
            }]
            
            try:
                checkout_session = gift_card_payment(line_item, success_url, cancel_url, sender_email)
                
                gift_card_table = UserGiftCard()

                if gift_card_id:
                    gift_card_table.gift_card_id = gift_card_id
                
                gift_card_table.gift_card_type = "GIFT_CARD"
                gift_card_table.giftcard_image_id = giftcard_image_id
                gift_card_table.sender_email = sender_email
                gift_card_table.gift_code = gift_code
                gift_card_table.receiver_email = receiver_email
                gift_card_table.receiver_name = username
                gift_card_table.title = title
                gift_card_table.user_message = message
                gift_card_table.is_paid = False
                gift_card_table.payment_intent_id = checkout_session.payment_intent
                gift_card_table.save()

                gift_card_table.expiry_date()
                
                request.session['gift_code'] = gift_code
                request.session.modified = True
                return JsonResponse({'sessionId': checkout_session['id']})
            except stripe.error.CardError as e:
                messages.error(request, e.user_message)
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(request, "Too many requests, please try again after sometimes")
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(request, "Invalid Request")
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(request, "Something Went Wrong")
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.error(request, "Failed to Connect with Stripe")
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.error(request, "Transaction Failed, Please Try Again")
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.error(request, "Something Went Wrong")
            return JsonResponse({'success': False, 'message': "Something Went Wrong"})

    return render(request, 'pages/gift-card.html',{'giftcard_type_images': giftcard_type_images, 'giftcard_type': giftcard_type,  'data':data, 'STRIPE_PUB_KEY': settings.STRIPE_PUBLIC_KEY, 'gift_card_images': gift_card_images, 'subscription_plans': subscription_plans, 'subscription_benefits': subscription_benefits})


def create_shero_gift_card(request):
    data = GiftCard.objects.all()
    gift_card_images = GiftCardImage.objects.all()
    giftcard_type = GiftCardType.objects.filter(is_active = True)
    giftcard_type_images = GiftCardTypeImages.objects.all()
    
    subscription_plans = SubscriptionPlan.objects.filter(is_active=True)
    if request.method=='POST':
        data_dict = json.loads(request.body)
        
        plan_id = data_dict.get('plan_id')
        receiver_email = data_dict.get('receiver_email').lower()
        re_enter_receiver_email = data_dict.get('re_enter_receiver_email').lower()
        title = data_dict.get('title')
        message = data_dict.get('message')
        username = data_dict.get('username')
        sender_email_id = data_dict.get("sender_email").lower()
        
        if sender_email_id:
            sender_email = sender_email_id
        else:
            if request.user.is_authenticated:
                sender_email = request.user.email.lower()

        if not sender_email:
            return JsonResponse({'success': False, 'message': 'Your Email is required'})
        elif sender_email == receiver_email:
            return JsonResponse({'success': False, 'message': "Recipient's email and Your email can't be same"})
        elif not plan_id:
            return JsonResponse({'success': False, 'message': 'Please Select a Plan'})
        elif len(message) > 700:
            return JsonResponse({'success': False, 'message': 'Message cannot be greater than 700 character'})

        # giftcard_image_id = data_dict.get("giftcard_image_id")
        
        # if not giftcard_image_id:
        #     return JsonResponse({'success': False, 'message': 'Please Select Gift Card Image'})
        
        if receiver_email != re_enter_receiver_email:
            return JsonResponse({'success': False, 'message': 'Receiver Emails Do Not Match'})

        if receiver_email == sender_email and re_enter_receiver_email == sender_email:
            return JsonResponse({'success': False, 'message': 'Receiver Email and Sender Email Cannot be Same'})
        
        if not (receiver_email and not receiver_email.isspace() and message and not message.isspace()):
            return JsonResponse({'success': False, 'message': 'All Fields Are Required!!!'})
        else:
            gift_code = random_with_N_digits(16)
            plan = subscription_plans.get(id=plan_id)
            success_url = 'success_payment_for_gift_card/'
            cancel_url = 'create_gift_card/'
            line_item = [{
                'name': f"{plan.plan_type} Shero Subscription Gift Card.",
                'currency': 'usd',
                'amount': int(float(plan.original_price) * 100),
                'quantity': 1,
            }]
            
            try:
                checkout_session = gift_card_payment(line_item, success_url, cancel_url, customer_email=sender_email)
                
                gift_card_table = UserGiftCard()

                if plan_id:
                    gift_card_table.subscription_plan_id = plan_id
                
                gift_card_table.gift_card_type = "SHERO_SUBSCRIPTION_GIFT_CARD"
                # gift_card_table.giftcard_image_id = giftcard_image_id
                gift_card_table.sender_email = sender_email
                gift_card_table.gift_code = gift_code
                gift_card_table.receiver_email = receiver_email
                gift_card_table.receiver_name = username
                gift_card_table.title = title
                gift_card_table.user_message = message
                gift_card_table.is_paid = False
                gift_card_table.payment_intent_id = checkout_session.payment_intent
                gift_card_table.save()
                gift_card_table.expiry_date()
                
                request.session['gift_code'] = gift_code
                request.session.modified = True
                return JsonResponse({'sessionId': checkout_session['id']})
            except stripe.error.CardError as e:
                messages.error(request, e.user_message)
            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(request, "Too many requests, please try again after sometimes")
            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(request, "Invalid Request")
            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(request, "Something Went Wrong")
            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.error(request, "Failed to Connect with Stripe")
            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.error(request, "Transaction Failed, Please Try Again")
            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.error(request, "Something Went Wrong")
            return JsonResponse({'success': False, 'message': "Something Went Wrong"})

    return render(request, 'pages/gift-card.html',{'giftcard_type_images': giftcard_type_images, 'giftcard_type': giftcard_type,  'data':data, 'STRIPE_PUB_KEY': settings.STRIPE_PUBLIC_KEY, 'gift_card_images': gift_card_images, 'subscription_plans': subscription_plans})
    

def success_payment_for_gift_card(request):
    gift_code = request.session.get('gift_code', None)
    if gift_code:
        user_gift_card = UserGiftCard.objects.get(gift_code=gift_code)
        sender_email_id = user_gift_card.sender_email.lower()
        if User.objects.filter(email = sender_email_id).exists():
            sender_email = User.objects.get(email = sender_email_id).email.lower()
        else:
            sender_email = sender_email_id

        del request.session['gift_code']
        request.session.modified = True

        intent = get_payment_intent(user_gift_card.payment_intent_id)
        if intent.status == 'succeeded':
            user_gift_card.stripe_charge_id = intent.charges.data[0].id
            user_gift_card.balance_transaction = intent.charges.data[0].balance_transaction
            user_gift_card.payment_method = intent.charges.data[0].payment_method
            user_gift_card.reciept_url = intent.charges.data[0].receipt_url
            user_gift_card.payment_intent = intent.charges.data[0].payment_intent
            user_gift_card.payment_method_types = intent.payment_method_types
            user_gift_card.customer = intent.customer
            user_gift_card.status = intent.status
            user_gift_card.amount = float(intent.amount/100)
            user_gift_card.save()
            
            receiver_email = user_gift_card.receiver_email.lower()
            message = user_gift_card.user_message

            if intent.charges.data[0].get('billing_details') and intent.charges.data[0].get('billing_details').get('name', None):
                sender_name =intent.charges.data[0].billing_details.name
            elif User.objects.filter(email=sender_email).exists():
                sender_name = User.objects.get(email=sender_email).name
            else:
                sender_name = "Megadolls User"

            # username = user_gift_card.receiver_name
            # giftcard_code = user_gift_card.gift_code
            if user_gift_card.gift_card_type == 'GIFT_CARD':
                title = int(user_gift_card.title)
                image_id = user_gift_card.giftcard_image_id
            
                gift_card_image = GiftCardTypeImages.objects.get(id=image_id).images

                if gift_card_image:
                    img_url = f"{settings.MEDIA_URL}{gift_card_image}"
                else:
                    img_dict = {
                        1: "happy_birthday.png",
                        2: "sending_you_love.png",
                        3: "congratulations.png"
                    }
                    img_url = f"{settings.SITE_URL}static/images/e-card-banner/{img_dict.get(title)}"
                
                # making html img tag to send banner image on mail
                img_tag = f'<img src="{img_url}" width="100%" height="550px">'
                try:
                    send_mail_giftcard(img_url=img_tag, receiver_email=receiver_email, sender_email=sender_email, sender_message=message)
                    send_mail_giftcard_sender(receiver_email, sender_email, intent.charges.data[0].receipt_url, user_gift_card, sender_name=sender_name)
                except: 
                    pass
                messages.success(request, "Gift Card sent to receiver's email.")
                return redirect('create_gift_card')
            try:
                send_mail_shero_subscription_gift_recipient(subscription_plan=user_gift_card.subscription_plan.plan_type, receiver_email=receiver_email, sender_email=sender_email, sender_message=message)
                send_mail_shero_subscription_gift_sender(user_gift_card.subscription_plan.plan_type, receiver_email, sender_email, intent.charges.data[0].receipt_url, sender_name)
            except Exception as err:
                pass

            messages.success(request, "Shero Subscription Gift sent to receiver's email.")
            return redirect('create_gift_card')
    
    messages.error(request, "Something Went Wrong")
    return redirect('create_gift_card')
        

# render all gift cards which user created or get from other users
@login_required(login_url='web_login')
def redeem_my_gift_card(request):
    data = UserGiftCard.objects.filter(Q(status='succeeded'), Q(receiver_email=request.user.email.lower())).order_by('-id')
    return render(request, 'pages/my-gift-card.html',{'data':data})

# send the otp in email for redeem the gift card :
@login_required(login_url='web_login')
def redeem_otp(request):
    user = User.objects.get(id=request.user.id) 
    otp_code = random_with_N_digits(6)
    user.otp = otp_code
    user.save()
    send_redeem_otp(user, otp_code)
    return JsonResponse({'success': True, 'message': "OTP Sent to your mail"})

# After redeem the card Gift card amount add to the user wallet balance:
@login_required(login_url='web_login')
def gift_card_to_wallet(request):
    otp = request.POST.get('redeem_otp')
    gift_code = request.POST.get('gift_code')
    
    email = request.user.email.lower()
    if request.user.otp != otp:
        messages.error(request, "Wrong OTP")
        return redirect('redeem_my_gift_card')
    
    if UserGiftCard.objects.filter(gift_code=gift_code, receiver_email=email, is_used=False).exists():
        user_gift_card = UserGiftCard.objects.get(gift_code=gift_code, receiver_email=email, is_used=False)
        
        if datetime.now() < user_gift_card.expire_at:
            user_gift_card.is_used = True
            user_gift_card.used_at = datetime.now()
            user_gift_card.save()
            
            if user_gift_card.gift_card:
                request.user.wallet += user_gift_card.gift_card.gift_price
            else:
                request.user.wallet = float(request.user.wallet) + float(user_gift_card.amount)
            request.user.save()
            
            wallet_transacton = WalletTransaction()
            wallet_transacton.user_id = request.user.id
            if user_gift_card.gift_card:
                wallet_transacton.amount = user_gift_card.gift_card.gift_price
            else:
                wallet_transacton.amount = user_gift_card.amount
            wallet_transacton.remaining_wallet_balance = request.user.wallet
            wallet_transacton.amount_status = 'DEPOSIT'
            wallet_transacton.transaction_type = 'GIFTCARD'
            wallet_transacton.save()
            messages.success(request, "Gift Card Amount Added to Your Wallet")
            return redirect('redeem_my_gift_card')
        else:
            messages.error(request, "Gift Card Already Expire")
            return redirect('redeem_my_gift_card')
    else:
        messages.error(request, "No Gift Card to Redeem")
    return redirect('redeem_my_gift_card')
    

def may_like_product_add_cart(request,slug):
    try:
        may_like_product_id = get_shop_product_id(slug)
        may_like_quantity_check = check_quantity(request, may_like_product_id)
        if may_like_quantity_check == False:
            messages.error(request, NO_STOCK_MSG)
            return redirect('view_cart')

        if request.user.is_anonymous:
            add_to_cart_anonymous(request, may_like_product_id)
            return redirect('web_login')
        else:
            add_to_cart_user(request, may_like_product_id)
        messages.success(request, 'Product Added to cart')
    except:
        messages.error(request, 'Something Went Wrong')
     
    return redirect('view_cart')

def may_like_add_to_wishlish_cart(request, id):
    try:
        if request.user.is_authenticated:
            user_id = request.user.id
            if not Wishlist.objects.filter(user_id=user_id, shop_id=id).exists():
                Wishlist.objects.create(user_id=user_id, shop_id=id)
        else:
            messages.error(request, 'Please Login First')
    except:
        pass
    return redirect('view_cart')


def send_referral_email(request):
    user_id = request.user.id
    user = User.objects.get(id = user_id)
    site_url = settings.SITE_URL
    sign_up_url = 'referral_sign_up/'
    user_slug = user.slug
    email_from = user.email.lower()
    name = user.name
    email_to = request.POST.get('referral_email').lower()
    referral_link = site_url+sign_up_url+user_slug
    link = f"<a href='{referral_link}'>click</a>"
    reply = "i have attached a referral link to this mail, kindly use it to sign up on the Megadolls    " + link   
    message = "Hi, My name is " + name + ", " + reply
    subject, from_email, to = (
        "Megadolls Referral Link",
        settings.EMAIL_HOST_USER,
        email_to,
    )
    msg = EmailMultiAlternatives(subject, message, from_email, [to])
    msg.send()
    messages.success(request, "Referal Link Sent")
    return redirect('my_account_wallet')

# webhook of ship station order placed 
@csrf_exempt
def webhook_order_place(request):
    email = request.user.email.lower()
    send_mail_order_place(email)
    messages.success(request, "Order Place Successfully")
    return redirect('my_account_order') 

@csrf_exempt
def stripe_webhook(request):
    # stripe call it when user cancel susbcription or subscription got expire
    try:
        payload = json.loads(request.body)
        stripe_customer_id = payload['data']['object']['customer']
        user_subscription = UserSubscriptions.objects.get(customer_id=stripe_customer_id)
        user_subscription_history = UserSubscriberHistory.objects.get(subscription_id = user_subscription.subscription_id)
        user_subscription_history.status = False
        user_subscription_history.save()
        user_subscription.subscription_id = None
        user_subscription.shero_subscription = None
        user_subscription.start_at = None
        user_subscription.expire_at = None
        user_subscription.save()
        user_email = user_subscription.user.email.lower()
        name = user_subscription.user.name
        return JsonResponse({'success': True, 'message': 'Subscription Cancelled'})
    except:
        return JsonResponse({'success': False, 'message': 'Some Error Occurs'})
    

def social_media_icons(request):
    links = SocialMedia.objects.all().values()
    serializer = SocialMediaSerializer(links, many = True)
    return JsonResponse({'links': serializer.data})

def search_product(request):
    site_url = settings.SITE_URL

    search_word = request.GET.get("search_word")
    splited_search_word = search_word.split(' ')
    search_query = Q(name__icontains=search_word)
    for i in splited_search_word:
        search_query |= Q(name__icontains=i)
    shop_data = ShopProduct.objects.filter(search_query, is_active=True, is_delete=False)

    shop_product_images = ShopProductImage.objects.filter(shop_product__is_active=True, shop_product__is_delete=False)
    tmp = {}
    for i in shop_data:
            avg=Review.objects.filter(shopproduct_id=i.id).aggregate(Avg('rating'))
            tmp[i.id] = avg.get('rating__avg')
    image_sub_tables = ShopProductImageSubTable.objects.filter(
            shop_product_image__shop_product__is_active=True, 
            shop_product_image__shop_product__is_delete=False)
    imagine_data = ImagineProduct.objects.filter(name__icontains=search_word, 
    is_active=True, is_delete=False)
    imagine_product_images = ImagineProductImage.objects.filter(
            imagine_product__is_active=True, imagine_product__is_delete=False)
    imagine_image_sub_tables = ImagineProductImageSubTable.objects.filter(
            imagine_product_image__imagine_product__is_active=True, 
            imagine_product_image__imagine_product__is_delete=False)
    if not shop_data and not imagine_data:
        data = False
    else:
        data = True
            
    return render(request, "pages/search_product.html",
                                                     {"data": data,
                                                      "site_url": site_url,
                                                      "rating_avg": tmp,
                                                      "imagine_products": imagine_data,
                                                      "imagine_product_images": imagine_product_images,
                                                      "imagine_image_sub_tables": imagine_image_sub_tables,
                                                      "shop_products": shop_data,
                                                      "shop_product_images": shop_product_images,
                                                      "image_sub_tables": image_sub_tables
                                                      })
    

class ShipStationWebhook(APIView):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        url = data["resource_url"]
        headers = {"Content-Type": "application/json"}

        cid = settings.SHIP_STATION_USERNAME
        secret = settings.SHIP_STATION_PASSWORD
        
        ship_station_response = requests.get(
            auth=(cid, secret), url=url, headers=headers
        ).json()
        
        ship_station = None
        if "shipments" in ship_station_response:
            ship_station = ship_station_response["shipments"]
        if "orders" in ship_station_response:
            ship_station = ship_station_response["orders"]
        if ship_station:
            for orders in ship_station:
                if orders["orderNumber"].isnumeric():
                    order = ProductOrder.objects.filter(order_id=orders["orderNumber"])
                else: 
                    order = GuestUserData.objects.filter(order_id=orders["orderNumber"])

                if order.exists():
                    order = order.first()

                if data["resource_type"] == "ORDER_NOTIFY":
                    order.order_status = "Accepted"
                    if orders["shipByDate"]:
                        order.delivery_at = orders["shipByDate"]
                        
                if data["resource_type"] == "SHIP_NOTIFY":
                    trackid_url = (
                        "https://ssapi.shipstation.com/shipments?orderNumber="
                        + orders["orderNumber"]
                    )
                    track = requests.get(
                        auth=(cid, secret), url=trackid_url, headers=headers
                    ).json()
                    order.webhook_data = track
                    order.save()
                    url = None
                    if track["shipments"]:
                        for shipment in track["shipments"]:
                            if shipment["trackingNumber"]:
                                track_id = shipment["trackingNumber"]
                                if shipment["carrierCode"] == "stamps_com":
                                    url = (f'https://tools.usps.com/go/TrackConfirmAction?tRef=fullpage&tLabels={track_id}')
                                else:
                                    url = (
                                        "https://wwwapps.ups.com/WebTracking/"
                                        + "processInputRequest?"
                                        + "sort_by=status&tracknums_displayed=1"
                                        + "&TypeOfInquiryNumber=T&"
                                        + "loc=en_US&InquiryNumber1="
                                        + str(track_id)
                                        + "&track.x=0&track.y=0"
                                    )
                                    
                            if shipment["confirmation"]:
                                order.order_status = "Completed"
                                if hasattr(order, 'user_id'):
                                    refered_user_id = order.user_id

                                try:
                                    if UserReferral.objects.filter(user_to_id = refered_user_id, order_status = False).exists():
                                        referred_user_data = UserReferral.objects.filter(user_to_id = refered_user_id)
                                        referred_user_data.order_status = True
                                        referred_user_data.save()
                                        referrer_user_id = referred_user_data.user_from_id
                                        referrer_user_data = UserReferral.objects.filter(user_from_id = referrer_user_id, order_status = True).count()
                                        if referrer_user_data % 3 == 0:
                                            user_data = User.objects.get(id = refered_user_id)
                                            user_data.referral_reward_status = False
                                            dolls_to_get = referrer_user_data // 3
                                            recieved_dolls = user_data.dolls_got_count
                                            user_data.dolls_to_get_count = dolls_to_get - recieved_dolls
                                            user_data.save()
                                            time = timezone.now()
                                            dolls = user_data.dolls_to_get_count - user_data.dolls_got_count
                                            if referrer_user_data > 3:
                                                message = f"{user_data.name}, has become eligible to recieve {dolls} free doll"
                                            else:
                                                message = f"{user_data.name}, has become eligible to recieve {dolls} free doll"
                                            Notification.objects.create(referrer_id = referrer_user_id, message = message, notification_type = "REFERRER", recevied_at = time)
                                except:
                                    pass

                    if orders["shipDate"]:
                        order.delivery_at = orders["shipDate"]
                        order.order_status = "Shipped"
                        if hasattr(order, 'user_id'):
                            email = order.user.email.lower()
                        else:
                            email = order.email.lower()
                        send_mail_for_order_shipped(email, order.order_id, url)
                    order.tracking_url = url
                order.save()
        return Response({"status": False}, status=200)


def testing(request):
    return render(request, "email_html/account-signup-verification.html")
    # , welcome_mail_for_signing_up(email,name), otp_to_reset_password(otp,email,link), blog_subscription_confirmation(email), newsletter_confirmation(email), shero_dolls_subscription_confirmation(email,name), send_mail_subscription_cancel(email,name), send_mail_giftcard(img_url,receiver_email,sender_email,sender_message), send_mail_giftcard_sender(receiver_email,sender_email,receipt_url,gift_card,sender_name), send_mail_shero_subscription_gift_recipient(subscription_plan,receiver_email,sender_email,sender_message), send_mail_shero_subscription_gift_sender(subscription_plan,receiver_email,sender_email,receipt_url,sender_name), send_redeem_otp(user,otp), send_mail_order_place(email,order_id,order_date,amount_dict,is_user_authenticated,product_order), cancel_order(email,name,order_id), send_mail_for_order_shipped(email,order_id,tracking_url), send_mail_plan_discontinue(emails), mail_send_verify_otp(email,otp), mail_send_user_credential(email,password), send_verification_otp_for_sloper_guest_user(email,otp)

#     import ast
#     with open(r'web_app/email.py') as file:
#         node = ast.parse(file.read())

#     result = []
#     functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]
#     classes = [n for n in node.body if isinstance(n, ast.ClassDef)]

#     for function in functions:
#         result.append(show_info(function))

#     for class_ in classes:
#         methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
#         for method in methods:
#             result.append((class_.name + '.' + show_info(method)))

#     print(', '.join(result))
#     return JsonResponse("asasas")

# def show_info(functionNode):
#     function_rep = ''
#     function_rep = functionNode.name + '('

#     for arg in functionNode.args.args:
#         function_rep += arg.arg + ','

#     function_rep = function_rep.rstrip(function_rep[-1])
#     function_rep += ')'
#     return function_rep



def testing_success(request):
    sess = stripe.checkout.Session.retrieve('cs_test_b1ZgRk4co6QUpN3WPTGwmiUeHVxROxyj6tm42Vvphi2g4L2BgdC4khSDOI')


def unsubscribe_to_blog(request, encrptyed_email):
    try:
        email = text_decryption(encrptyed_email).lower()
        message = "You are succesfully unsubscribed to Megadolls's 'A Meaningful Play'."
        success = True
        email = email.lower()
        BlogSubscriber.objects.filter(email=email).delete()
        return render(request, "pages/unsubscribe_successful.html", {'message': message, 'success': success})     
    except:
        message = "Something went wrong, please try again."
        return render(request, "pages/unsubscribe_successful.html", {'message': message})


def unsubscribe_to_newsletter(request, encrptyed_email):
    try:
        email = text_decryption(encrptyed_email).lower()
        message = "You are succesfully unsubscribed to Megadolls's Newsletters."
        success = True
        email = email.lower()
        Newsletters.objects.filter(email=email).delete()
        return render(request, "pages/unsubscribe_successful.html", {'message': message, 'success': success})     
    except:
        message = "Something went wrong, please try again."
        return render(request, "pages/unsubscribe_successful.html", {'message': message})  


def register_guest_user(request):
    if request.session.has_key('guest_user'):
        del request.session['guest_user']
        request.session.modified = True

    try:
        if request.method == 'POST':
            guest_email = request.POST.get('guest_email').lower()
            if not guest_email:
                messages.error(request, 'Please Enter Email')
                return redirect('view_cart')
            
            if User.objects.filter(email=guest_email).exists():
                messages.error(request, "You are a registered customer please login as registered Customer")
                return redirect('view_cart')

            order_id = generate_order_id(10)
            while GuestUserData.objects.filter(order_id=order_id).exists():
                    order_id = generate_order_id(10)
                    
            guest_user_data = GuestUserData()
            guest_user_data.email = guest_email
            guest_user_data.order_id = order_id
            guest_user_data.save()
            request.session['guest_user'] = { 'order_id': str(guest_user_data.order_id) }
            request.session.modified = True
            return redirect('guest_user_billing')
        else:
            return redirect('view_cart')
    except:
        messages.error(request, 'Something went wrong')
        return redirect('view_cart')


def guest_user_billing(request):
    try:
        # if request.META.get('HTTP_REFERER') and (reverse('guest_user_billing') not in request.META.get('HTTP_REFERER') or reverse('add_guest_user_address') not in request.META.get('HTTP_REFERER')):
        #     if request.META.get('HTTP_REFERER') == None or reverse('view_cart') not in request.META.get('HTTP_REFERER'):
        #         return redirect('view_cart')
        if request.user.is_authenticated:
            return redirect('view_cart')

        if not request.session.has_key('guest_user'):
            messages.error(request, "Please sign in or login as guest")
            return redirect('view_cart')

        shipping_prices = ShippingPrice.objects.all()
        sub_total = float(cart_sub_total(request))
        shipping_price_range = get_shipping_price_range(shipping_prices, sub_total)

        order_id = request.session['guest_user']['order_id']
        guest_user = GuestUserData.objects.filter(order_id=order_id).first()

        guest_user.total_amount = round(sub_total + float(shipping_price_range.shipping_cost), 2)
        guest_user.shipping_charge = round(float(shipping_price_range.shipping_cost), 2)
        guest_user.save()

        data = {
            # 'carriers': carriers, 
            'sub_total': sub_total,
            'guest_user_address': guest_user,
            'countries': WebCountry.objects.all(),
            'shipping_prices': shipping_prices,
            'shipping_price_range': shipping_price_range,
            'grand_total': round(sub_total + float(guest_user.shipping_charge), 2)
        }
        return render(request, 'pages/guest/billing.html', data)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('view_cart')


def add_guest_user_address(request):
    if not request.session.has_key('guest_user'):
        return redirect('view_cart')
        
    order_id = request.session['guest_user']['order_id']
    guest_user_data = GuestUserData.objects.filter(order_id=order_id)
    if guest_user_data:
        guest_user_data = guest_user_data.first()
        guest_user_data.shipping_address = {
            'name': request.POST.get('name'),
            'house_number': request.POST.get('house_number'),
            'area_name': request.POST.get('area_name'),
            'country': WebCountry.objects.get(id=request.POST.get('country')).short_name,
            'state': WebState.objects.get(id=request.POST.get('state')).name,
            'city': request.POST.get('city'),
            'zipcode': request.POST.get('zipcode'),
            'phone': request.POST.get('phone'),
        }
        guest_user_data.billing_address = guest_user_data.shipping_address
        guest_user_data.save()
        messages.success(request, 'Address Added')
        return redirect('guest_user_billing')
    else:
        messages.error(request, 'Failed to add address')
        return redirect('guest_user_billing')


def guest_user_create_checkout_session(request):
    if request.method == 'POST':
        if not request.session.has_key('guest_user'):
            return JsonResponse({'status': False, 'message': 'Guest User Not Exist'})

        if request.session.has_key('payment_intent_id'):
            del request.session['payment_intent_id']
            request.session.modified = True
        
        try:
            order_id = request.session['guest_user']['order_id']
            guest_user_data = GuestUserData.objects.filter(order_id = order_id)
            if guest_user_data:
                guest_user_data = guest_user_data.first()

                total_quantity = 0
                for data in guest_user_data.order_detail:
                    # total_amount += float(data.get('amount'))
                    total_quantity += data.get('quantity')

                # total_amount += float(guest_user_data.shipping_charge)
                domain = settings.SITE_URL
                stripe.api_key = settings.STRIPE_SECRET_KEY
                checkout_session = stripe.checkout.Session.create(
                    customer_email=guest_user_data.email.lower(),
                    payment_method_types=["card"],
                    mode = 'payment',
                    success_url = domain + f"guest-user-stripe-success/",
                    cancel_url = domain + "cancelled/",
                    # line_items=[
                    #     {
                    #         'name': "total quantity of Product " + str(total_quantity),
                    #         'currency': 'usd',
                    #         'amount': int(float(guest_user_data.total_amount) * 100),
                    #         'quantity': 1,
                    #     },
                    # ],
                    line_items = [{
                        "quantity": 1,
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(float(guest_user_data.total_amount) * 100),
                            "tax_behavior": "exclusive",
                            "product_data": {
                                "name": "total quantity of Product " + str(total_quantity),
                                "tax_code": STRIPE_TAX_CODE['product'],
                            }
                        }
                    }],
                    automatic_tax={
                        'enabled': True,
                    },
                )

                request.session['checkout_session_id'] = checkout_session['id']
                request.session['payment_intent_id'] = checkout_session.payment_intent
                request.session.modified = True
                return JsonResponse({'sessionId': checkout_session['id']})
            else:
                return JsonResponse({'status': False, 'message': 'Guest User Not Exists'})

        except stripe.error.CardError as e:
            return JsonResponse({'message': e.user_message})
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            return JsonResponse({'message': 'Too many requests, please try again after sometimes'})
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            return JsonResponse({'message': 'Invalid Request'})
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            return JsonResponse({'message': 'Something Went Wrong'})
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            return JsonResponse({'message': 'Failed to Connect with Stripe'})
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            return JsonResponse({'message': 'Transaction Failed, Please Try Again'})
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            return JsonResponse({'message': 'Something Went Wrong'})


def guest_user_stripe_success(request):
    try:
        try:
            check_all_quantity(request)
        except Exception as err:
            messages.error(request, err)
            return redirect('view_cart')

        data = None 
        product_data = None
        order_id = request.session['guest_user']['order_id']
        guest_user_data = GuestUserData.objects.filter(order_id=order_id)
        if guest_user_data:
            guest_user_data = guest_user_data.first()
        else:
            messages.error(request, "Guest User Not Exist")
            return redirect('view_cart')

        # if request.session.has_key('guest_user') and request.session.has_key('guest_user_data'):
        #     order_data =  request.session['guest_user']['guest_user_data']
        #     # tax = order_data.get('tax')
        #     shipment_cost = order_data.get('shipment_cost')
        #     sub_total = order_data.get('sub_total')
        #     total_amount = order_data.get('total_amount')
        # else:
        tax = float(guest_user_data.tax)
        total_amount = float(guest_user_data.total_amount)
        shipment_cost = float(guest_user_data.shipping_charge)
        sub_total = total_amount - float(guest_user_data.shipping_charge) - tax
        
        email = guest_user_data.email.lower()
        name = guest_user_data.shipping_address.get('name')
        phone = guest_user_data.shipping_address.get('phone')
        has_payment_intent_id = request.session.has_key('payment_intent_id')
        
        if has_payment_intent_id:
            payment_intent_id = request.session.get('payment_intent_id', None)
            intent = get_payment_intent(payment_intent_id)

            checkout_session = retrive_checkout_session(request.session.get('checkout_session_id', None))
            tax = (checkout_session.total_details.amount_tax / 100)

            del request.session['payment_intent_id']
            del request.session['checkout_session_id']
            request.session.modified = True
            if request.session.has_key('anonymous_user'):
                a_id = request.session['anonymous_user']['a_id']
                cart = AnonymousCart.objects.filter(a_id=a_id)
                if cart:
                    cart = cart.first()
                    product_list = string_to_list(cart.shop_product_list)
                    cart.delete()
                    product_dict = dict(Counter(product_list))
                    product_data = ShopProduct.objects.filter(id__in=product_list)
            
                    # substracting product quantity from available stock which user buy 
                    for product in product_data:
                        product.available_quantity -= product_dict.get(product.id)
                        product.save()
                
                guest_user_data.stripe_payment_data = {
                    'stripe_charge_id': intent.charges.data[0].id,
                    'balance_transaction': intent.charges.data[0].balance_transaction,
                    'amount': intent.charges.data[0].amount / 100,
                    'payment_method': intent.charges.data[0].payment_method,
                    'card_brand': intent.charges.data[0].payment_method_details.card.brand,
                    'reciept_url': intent.charges.data[0].receipt_url,
                    'status': intent.charges.data[0].status,
                    'payment_intent': intent.charges.data[0].payment_intent,
                    'payment_method_types': intent.payment_method_types,
                    'customer': intent.customer
                }
                guest_user_data.tax = tax
                total_amount = float(guest_user_data.total_amount) + float(tax)
                guest_user_data.total_amount = total_amount
                guest_user_data.order_at = datetime.now()
                guest_user_data.delivered_at = guest_user_data.get_delivery_date()
                guest_user_data.save()

                # creating order for ship station api
                guest_user_create_order(guest_user_data)

                try:
                    amount_dict = {'stripe': total_amount}
                    send_mail_order_place(email, order_id, guest_user_data.order_at, amount_dict, request.user.is_authenticated)
                except:
                    pass
                try:
                    order_confirmation_sms(name, phone, order_id)
                except:
                    pass

        data = {
            'shipping_address': guest_user_data.shipping_address,
            'order_id': guest_user_data.order_id,
            'order_at': guest_user_data.order_at,
            'tax': tax,
            'shipment_cost': shipment_cost,
            'sub_total': round(sub_total, 2),
            'total_amount': total_amount,
        }

        return render(request, 'pages/guest/order-confirmation.html', data)
    except Exception as err:
        messages.error(request, 'Something Went Wrong')
        return redirect('view_cart')


def guest_user_payment(request):
    if request.META.get('HTTP_REFERER') == None or reverse('guest_user_billing') not in request.META.get('HTTP_REFERER'):
        return redirect('guest_user_billing')
    elif request.user.is_authenticated:
        return redirect('view_cart')
    elif not request.session.has_key('guest_user') and not request.session.get('guest_user').has_key('guest_user_data'):
        messages.error(request, 'Something Went Wrong')
        return redirect('view_cart')

    guest_user_data = request.session['guest_user']['guest_user_data']
    data_dict = {
                'sub_total': guest_user_data.get('sub_total'),
                'shipment_cost': guest_user_data.get('shipment_cost'),
                'tax': guest_user_data.get('tax'),
                'total_amount': guest_user_data.get('total_amount'),
                'STRIPE_PUB_KEY': settings.STRIPE_PUBLIC_KEY,
                }
    return render(request, 'pages/guest/payment.html', data_dict)


def download_count_increment(request):
    try:
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        now_date = datetime.now()
        if not user.download_date:
            user.download_date = now_date
            user.download_count = 0
            user.save()
        if now_date-user.download_date >= timedelta(days=1):
            user.download_count = 0
            user.save()
        if user.download_count >= 1:
            return JsonResponse({"success": False, "message": "&#9825; Please come back after 24 hours to download another free dress! &#9825;"})   
        else:
            user.increase_download_count()
            # update_user = User.objects.get(id=user_id)
            return JsonResponse({"success": True, "message": f"&#9825; Please come back after 24 hours to download another free dress! &#9825;"})
    except:
        return JsonResponse({'success': False, "message": "something went wrong"})


def make_social_user_verified(request):
    request.user.is_verified = True
    request.user.save()
    return JsonResponse({"success": True, "message": "Verified"})


def render_sloper_landing_page(request):
    if not settings.DEBUG:
        return redirect('sloper_coming_soon')
    banner_image = SloperLandingPageBannerImage.objects.all().order_by('id')
    how_it_work = SloperLandingPageHowItWork.objects.first()
    how_it_work_sections = SloperLandingPageHowItWorkSection.objects.all()
    testimonial = SloperLandingPageTestimonial.objects.first()
    testimonial_sections = SloperLandingPageTestimonialSection.objects.all()
    individual_sloper = SloperPlanCategory.objects.get(category_title = "Individual Plan")
    individual_plan = {}
    individual_plan["category"] = individual_sloper
    individual_sloper_plans = SloperPlan.objects.filter(category_id = individual_sloper.id).order_by('id')
    individual_plan["plans"] = individual_sloper_plans
    individual_base_price = SloperBasicPrice.objects.get(category_id = individual_sloper.id)
    individual_plan["price_per_month"] = individual_base_price.price
    hospital_plan = {}
    hospital_sloper = SloperPlanCategory.objects.get(category_title = "Hospital")
    hospital_plan["category"] = hospital_sloper
    hospital_sloper_plans = SloperPlan.objects.filter(category_id = hospital_sloper.id).order_by('id')
    hospital_plan["plans"] = hospital_sloper_plans
    hospital_base_price = SloperBasicPrice.objects.get(category_id = hospital_sloper.id)
    hospital_plan["hospital_price"] = hospital_base_price.price 
    school_plan = {}
    school_sloper = SloperPlanCategory.objects.get(category_title = "School")
    school_plan["category"] = school_sloper
    school_sloper_plans = SloperPlan.objects.filter(category_id = school_sloper.id)
    school_plan["plans"] = school_sloper_plans 
    school_prices = []
    school_base_price = SloperBasicPrice.objects.filter(category_id = school_sloper.id)
    for price in school_base_price:
        school_prices.append(price)
    school_plan["school_price"] = school_prices
    return render(request, 'pages/sloper-subscription/sloper-landing-page.html', 
                        {  'individual_plan': individual_plan,
                           'hospital_plan': hospital_plan,
                           'school_plan': school_plan,
                           'banner_image': banner_image, 'how_it_work': how_it_work, 
                           'how_it_work_section': how_it_work_sections, 'testimonial': testimonial, 
                           'testimonial_sections': testimonial_sections  
                        })


def summary_sloper_individual_personal_plan(request):
    plan_name = request.POST["sloper_plan_type"]  
    individual_plan_id = request.POST['individual_plan_id']
    sloper_plan = SloperPlan.objects.get(id=individual_plan_id)
    month = interval_dict[sloper_plan.name]
    plan_category =  SloperPlanCategory.objects.get(category_title="Individual Plan")
    plan_basic_price = SloperBasicPrice.objects.get(category_id = plan_category.id)
    monthly_price = plan_basic_price.price
    total_price = float(month * monthly_price)
    discount = float(sloper_plan.data["off"]) 
    total_subscription_amount = total_price * (100 - discount) / 100
    request.session['sloper_user_plan_data'] = {
        "plan_data": {  "total_subscription_amount":total_subscription_amount,
                        "plan_name":plan_name,
                        "month":month,
                        "discount":discount,}
                     }
    request.session.modified = True
    return JsonResponse({"success": True})    


def summary_sloper_individual_gift_plan(request):
    recipient_name = request.POST["recipient_name"]
    recipient_email = request.POST["recipient_email"].lower()
    plan_name = request.POST["sloper_plan_type"]  
    individual_plan_id = request.POST['individual_plan_id']
    sloper_plan = SloperPlan.objects.get(id=individual_plan_id)
    month = interval_dict[sloper_plan.name]
    plan_category =  SloperPlanCategory.objects.get(category_title="Individual Plan")
    plan_basic_price = SloperBasicPrice.objects.get(category_id = plan_category.id)
    monthly_price = plan_basic_price.price
    total_price = float(month * monthly_price)
    discount = float(sloper_plan.data["off"]) 
    total_subscription_amount = total_price * (100 - discount) / 100
    print(total_subscription_amount, "==============================================")
    request.session['sloper_user_gift_plan_data'] = {
        "plan_data":{
            "total_subscription_amount":total_subscription_amount,
            "plan_name":plan_name,
            "month":month,
            "discount":discount,
            "recipient_name":recipient_name,
            "recipient_email":recipient_email,
        }
    }
    request.session.modified = True
    return JsonResponse({"success": True})  

def checkout_sloper_individual_personal_plan(request):
    sloper_user_plan_data = request.session['sloper_user_plan_data']
    total_subscription_amount = sloper_user_plan_data["plan_data"]["total_subscription_amount"]
    plan_name = sloper_user_plan_data["plan_data"]["plan_name"]  
    discount = sloper_user_plan_data["plan_data"]["discount"]
    original_price = float(total_subscription_amount) / (1-(float(discount)/100))
    discount_price = original_price-float(total_subscription_amount)
    plan_category = SloperPlanCategory.objects.get(category_title = "Individual Plan")
    return render(request, "pages/sloper-subscription/sloper-order-summary.html", {"plan_name": plan_name,"original_price":original_price,
    "discount_price":discount_price,"plan_category":plan_category,"discount":discount, "total_subscription_amount":total_subscription_amount})
    

def checkout_sloper_individual_gift_plan(request):
    sloper_user_plan_data = request.session["sloper_user_gift_plan_data"]
    total_subscription_amount = sloper_user_plan_data["plan_data"]["total_subscription_amount"]
    recipient_name = sloper_user_plan_data["plan_data"]["recipient_name"]
    recipient_email = sloper_user_plan_data["plan_data"]["recipient_email"].lower()
    plan_name = sloper_user_plan_data["plan_data"]["plan_name"]  
    discount = sloper_user_plan_data["plan_data"]["discount"]
    original_price = float(total_subscription_amount) / (1-(float(discount)/100))
    discount_price = original_price-float(total_subscription_amount)
    plan_category = SloperPlanCategory.objects.get(category_title = "Individual Plan")
    return render(request, "pages/sloper-subscription/sloper-order-summary.html", {"original_price":original_price,"plan_name": plan_name,"discount":discount,
    "discount_price":discount_price,"plan_category":plan_category,"recipient_email":recipient_email,"recipient_name":recipient_name,
    "total_subscription_amount":total_subscription_amount})
    

# individual personal
def add_sloper_personal_plan_type(request):
    one_time_or_recurring = request.POST["one_time_or_recurring"]
    sloper_plan_session = request.session["sloper_user_plan_data"]
    sloper_plan_session['plan_type'] = one_time_or_recurring
    request.session.modified = True
    is_user_has_active_subscription = UserSloperSubscription.objects.filter(category='Individual', user_id=request.user.id, is_active=True).exists()
    if is_user_has_active_subscription:
        return JsonResponse({"success": False, "user_has_active": is_user_has_active_subscription, "message": "You already have active subscription"})
    return JsonResponse({"success": True, "user_has_active": is_user_has_active_subscription})

# individual personal
def add_sloper_gift_plan_type(request):
    one_time_or_recurring = request.POST["one_time_or_recurring"]
    sloper_plan_session = request.session["sloper_user_gift_plan_data"]
    sloper_plan_session['plan_type'] = one_time_or_recurring
    request.session.modified = True
    return JsonResponse({"success": True})

# individual personal
def add_sloper_personal_billing_address(request):
    countries = WebCountry.objects.all()
    return render(request, 'pages/sloper-subscription/sloper-personal-billing-address.html', {"countries": countries})  


def add_sloper_gift_billing_address(request):
    countries = WebCountry.objects.all()
    return render(request, 'pages/sloper-subscription/sloper-gift-billing-address.html', {"countries": countries})     

def create_sloper_billing_address(address: dict):
    return SloperBillingAddress.objects.create(
        first_name=address["first_name"],
        last_name=address["last_name"],
        country=address["country"],
        phone_number=address["phone_number"],
        zipcode=address["zipcode"],
        city=address["city"],
        state=address["state"],
        street=address["street"]
    )

def get_sloper_billing_address_from_post_request(post_request):
    return {
        'first_name': post_request['first_name'],
        'last_name': post_request['last_name'],
        'country': post_request['country'],
        'phone_number': post_request['phone_number'],
        'street': post_request['address'],
        'zipcode': post_request['zipcode'],
        'city': post_request['city'],
        'state': post_request['state'],
    }

def get_stripe_data_for_sloper_subscription(stripe_payment_intent_id):
    intent = get_payment_intent(stripe_payment_intent_id)
    receipt_url = intent.charges.data[0].receipt_url
    stripe_data = {
        'stripe_charge_id': intent.charges.data[0].id,
        'balance_transaction': intent.charges.data[0].balance_transaction,
        'payment_method': intent.charges.data[0].payment_method,
        'card_brand': intent.charges.data[0].payment_method_details.card.brand,
        'status': intent.charges.data[0].status,
        'payment_intent': intent.charges.data[0].payment_intent,
        'payment_method_types': intent.payment_method_types,
    }
    return {'receipt_url': receipt_url, 'stripe_data': stripe_data}

def stripe_sloper_individual_personal_plan(request):
    sloper_personal_plan_session = request.session["sloper_user_plan_data"]
    total_subscription_amount = sloper_personal_plan_session["plan_data"]["total_subscription_amount"]
    total_amount_on_stripe = int(float(total_subscription_amount) * 100)

    month = sloper_personal_plan_session["plan_data"]["month"]
    plan_type = sloper_personal_plan_session["plan_type"]

    success_url = 'sloper-personal-order-confirmation/'
    cancel_url = 'render_sloper_landing_page/'

    user_id = request.user.id
    user_subscription = UserSubscriptions.objects.get(user_id = user_id)
    customer_id = user_subscription.customer_id
    
    if plan_type == "RECURRING":
        plan_name = sloper_personal_plan_session["plan_data"]["plan_name"] 
        description = "Sloper Individual Subscription"
        product_on_stripe = create_product(plan_name, description)
        sloper_personal_plan_session['product_on_stripe_id'] = product_on_stripe['id']

        recurring = {"interval": "month", "interval_count": month}
        price_on_stripe = create_subscription_price(amount=total_amount_on_stripe, recurring=recurring, stripe_product_id=product_on_stripe.id)
        sloper_personal_plan_session['price_on_stripe_id'] = price_on_stripe['id']

        line_items = [{"price": price_on_stripe.id,"quantity":1}]
        payment_sloper_subscription = payment_for_subscription(line_items=line_items, success_url=success_url,
        cancel_url=cancel_url, user_id = user_id, customer_id=customer_id)
    elif plan_type == "ONE_TIME":
        line_items = [{
            'name': f"Sloper Individual Subscription for {month} month",
            'currency': 'usd',
            'amount': total_amount_on_stripe,
            'quantity': 1,
        }]
        payment_sloper_subscription = payment_for_subscription(line_items=line_items, success_url=success_url,
        cancel_url=cancel_url, user_id = user_id, customer_id=customer_id, mode='payment')

        sloper_personal_plan_session['payment_intent_id'] = payment_sloper_subscription['payment_intent']

    sloper_personal_plan_session['checkout_session_id'] = payment_sloper_subscription['id']
    sloper_personal_plan_session['sloper-billing-address'] = get_sloper_billing_address_from_post_request(request.POST)
    request.session.modified = True
    return JsonResponse({"success":True, "sessionId":payment_sloper_subscription['id']})
  
def stripe_sloper_individual_gift_plan(request):
    sloper_gift_plan_session = request.session["sloper_user_gift_plan_data"]
    total_subscription_amount = sloper_gift_plan_session["plan_data"]["total_subscription_amount"]
    total_amount_on_stripe = int(float(total_subscription_amount) * 100)

    month = sloper_gift_plan_session["plan_data"]["month"]
    line_items = [{
        'name': f"Sloper Subscription for Individual for {month} month",
        'currency': 'usd',
        'amount': total_amount_on_stripe,
        'quantity': 1,
    }]

    user_id = request.user.id
    user_subscription = UserSubscriptions.objects.get(user_id = user_id)
    customer_id = user_subscription.customer_id
    success_url = 'sloper-gift-order-confirmation/'
    cancel_url = 'render-sloper-landing-page/'
    payment_sloper_subscription = payment_for_subscription(line_items=line_items, success_url=success_url, cancel_url=cancel_url, user_id=user_id, customer_id=customer_id, mode='payment')

    sloper_gift_plan_session['checkout_session_id'] = payment_sloper_subscription['id']
    sloper_gift_plan_session['payment_intent_id'] = payment_sloper_subscription['payment_intent']
    sloper_gift_plan_session['sloper-billing-address'] = get_sloper_billing_address_from_post_request(request.POST)
    request.session.modified = True
    return JsonResponse({"success":True, 'sessionId':payment_sloper_subscription['id']}) 

# sloper individual personal
def sloper_personal_order_confirmation(request):
    user_id = request.user.id
    try:
        user_subscription = UserSubscriptions.objects.get(user_id=user_id)
    except UserSubscriptions.DoesNotExist:
        messages.error(request, "Something Went Wrong")
        return render(request, 'pages/sloper-subscription/sloper-personal-order-confirmation.html')
    customer_id = user_subscription.customer_id
    sloper_personal_session_data = request.session["sloper_user_plan_data"]
    plan_data = sloper_personal_session_data["plan_data"]
    address = sloper_personal_session_data["sloper-billing-address"]
    plan_type = sloper_personal_session_data["plan_type"] 
    discount = plan_data["discount"]
    original_price = float(plan_data["total_subscription_amount"]) / (1-(float(discount)/100))
    discount_price = original_price-float(plan_data["total_subscription_amount"])
    checkout_session = retrive_checkout_session(sloper_personal_session_data['checkout_session_id'])
    sloper_stripe_data = SloperStripeData()
    sloper_stripe_data.email = request.user.email.lower()
    sloper_stripe_data.customer_id=customer_id

    if plan_type == "RECURRING":
        recurring = True
        sloper_stripe_data.stripe_product_id = sloper_personal_session_data["product_on_stripe_id"]
        sloper_stripe_data.stripe_price_id = sloper_personal_session_data["price_on_stripe_id"]
        checkout_session = retrive_checkout_session(sloper_personal_session_data['checkout_session_id'])
        sloper_stripe_data.subscription_id = checkout_session.subscription
    else:
        recurring = False
        payment_intent_id = sloper_personal_session_data['payment_intent_id']
        stripe_data = get_stripe_data_for_sloper_subscription(payment_intent_id)
        sloper_stripe_data.reciept_url = stripe_data['receipt_url']
        sloper_stripe_data.stripe_data = stripe_data['stripe_data']
    sloper_stripe_data.save()

    sloper_billing_address = create_sloper_billing_address(address)

    UserSloperSubscription.objects.create(
        category="Individual",
        user_id=request.user.id,
        sloper_stripe_data_id=sloper_stripe_data.id,
        plan_detail={
            "name": plan_data["plan_name"],
            "price": plan_data["total_subscription_amount"],
            "discount": plan_data["discount"],
            "discount_price": discount_price,
            "original_price" : original_price
        },
        is_recurring=recurring,
        billing_address_id=sloper_billing_address.id,
        is_active=True,
        start_at=timezone.now(),
        is_gifted=False
    )
    return render(request, 'pages/sloper-subscription/sloper-personal-order-confirmation.html')

def sloper_gift_order_confirmation(request):
    user_id = request.user.id
    user_subscription = UserSubscriptions.objects.get(user_id = user_id)
    customer_id = user_subscription.customer_id

    sloper_gift_plan_session = request.session["sloper_user_gift_plan_data"]
    plan_data = sloper_gift_plan_session["plan_data"]
    address = sloper_gift_plan_session["sloper-billing-address"]
    plan_type = sloper_gift_plan_session["plan_type"]
    interval_count = sloper_gift_plan_session["plan_data"]["month"]
    plan_name = sloper_gift_plan_session["plan_data"]["plan_name"] 

    total_subscription_amount = sloper_gift_plan_session["plan_data"]["total_subscription_amount"]
    total_amount_on_stripe = int(float(total_subscription_amount) * 100)
    discount = plan_data["discount"]
    original_price = float(total_subscription_amount) / (1-(float(discount)/100))
    discount_price = original_price-float(total_subscription_amount)

    sloper_stripe_data = SloperStripeData()
    sloper_stripe_data.email = request.user.email.lower()
    sloper_stripe_data.customer_id=customer_id

    if plan_type == "RECURRING":
        is_recurring = True

        description = "Gift Sloper Individual Subscription"
        stripe_product = create_product(plan_name, description)

        recurring_dict = {"interval":"month", "interval_count":interval_count}
        stripe_subscription_price = create_subscription_price(amount=total_amount_on_stripe, recurring=recurring_dict, stripe_product_id=stripe_product["id"])

        date_after_one_month = int(get_unix_timestamp_of_one_month_later())
        subscription_schedule = create_subscription_schedule(customer_id=customer_id, start_date=date_after_one_month, price_id=stripe_subscription_price["id"])

        sloper_stripe_data.stripe_product_id = stripe_product["id"]
        sloper_stripe_data.stripe_price_id = stripe_subscription_price["id"]
        sloper_stripe_data.schedule_subscription_id = subscription_schedule['id']
    else:
        is_recurring = False

    payment_intent_id = sloper_gift_plan_session['payment_intent_id']
    
    stripe_data = get_stripe_data_for_sloper_subscription(payment_intent_id)

    sloper_stripe_data.reciept_url = stripe_data.get('receipt_url')
    sloper_stripe_data.stripe_data = stripe_data.get('stripe_data')
    sloper_stripe_data.save()

    sloper_billing_address = create_sloper_billing_address(address)
    
    user_sloper_subscription = UserSloperSubscription.objects.create(
        category="Individual",
        sloper_stripe_data_id=sloper_stripe_data.id,
        plan_detail={
            "name": plan_data["plan_name"],
            "price": plan_data["total_subscription_amount"],
            "original_price" : original_price,
            "discount": plan_data["discount"],
            "discount_price": discount_price
        },
        is_recurring=is_recurring,
        billing_address_id=sloper_billing_address.id
    )

    UserGiftSloperPlan.objects.create(
        sender_user_id=request.user.id,
        receiver_email=plan_data["recipient_email"].lower(),
        user_detail={
            "recipient_name":  plan_data["recipient_name"]
        },
        is_wasted=False,
        user_sloper_subscription_id=user_sloper_subscription.id
    )
    return render(request, 'pages/sloper-subscription/sloper-gift-order-confirmation.html')

def sloper_personal_order_details(request):
    sloper_personal_session_data = request.session["sloper_user_plan_data"]
    address = sloper_personal_session_data["sloper-billing-address"]
    plan_type = sloper_personal_session_data["plan_type"]
    plan_detail = sloper_personal_session_data["plan_data"]
    total_subscription_amount = sloper_personal_session_data["plan_data"]["total_subscription_amount"]
    discount = sloper_personal_session_data["plan_data"]["discount"]
    original_price = float(total_subscription_amount) / (1-(float(discount)/100))
    discount_price = original_price-float(total_subscription_amount)
    return render(request, "pages/sloper-subscription/sloper-persoanl-order-detail.html", {"address": address, "plan_type":plan_type, "plan_detail":plan_detail
    ,"original_price": original_price, "discount": discount, "discount_price": discount_price})


def sloper_gift_order_details(request):
    sloper_gift_session_data = request.session["sloper_user_gift_plan_data"]
    address = sloper_gift_session_data["sloper-billing-address"]
    plan_type = sloper_gift_session_data["plan_type"]
    plan_detail = sloper_gift_session_data["plan_data"]
    total_subscription_amount = sloper_gift_session_data["plan_data"]["total_subscription_amount"]
    discount = sloper_gift_session_data["plan_data"]["discount"]
    original_price = float(total_subscription_amount) / (1-(float(discount)/100))
    discount_price = original_price-float(total_subscription_amount)
    return render(request, "pages/sloper-subscription/sloper-gift-order-detail.html", {"address": address,
    "plan_type":plan_type, "plan_detail":plan_detail, "discount_price":discount_price, "original_price":original_price, "discount":discount})


def sloper_checkout_login(request):
    email = request.POST.get('email').lower()
    password = request.POST.get('password')
    user = User.objects.filter(email=email, is_delete=False)
    if user.filter(is_verified=True).exists():
        verified_user = user.filter(is_verified=True).first()
        if verified_user.check_password(password):
            login(request, verified_user)
            return JsonResponse({"success": True})
    else:
        non_verified_user = user.filter(is_verified=False).first()
        verify_mail(non_verified_user)
        non_verified_user.is_mail_send = True
        non_verified_user.save()
        return JsonResponse({"success": False, "message": "Your Account is not Verified, Verification link sent to your Email"})


def sloper_guest_user_checkout_login(request):
    email = request.POST["sloper_guest_user_email"].lower()
    if User.objects.filter(email=email).exists():
        verified_user = User.obejcts.get(email=email)
        login(request, verified_user)
    else:
        user = User.objects.create(email=email, is_verified= True)
        customer = create_customer(email)
        subscription_data = UserSubscriptions(user_id=user.id, customer_id=customer['id'])
        subscription_data.save()
        login(request, user)    
    return JsonResponse({"success": True})   


def verification_otp_for_sloper_guest_user(request):
    email = request.POST["sloper_guest_user_email"].lower()
    otp = randint(1111, 9999)
    send_verification_otp_for_sloper_guest_user(email, otp)
    return JsonResponse({"success": True, "otp": otp})
        

def save_sloper_hospital_data(request):
    patient_count = int(request.POST["patient_count"])
    hospital_plan_id = request.POST['hospital_plan_id']
    plan_category =  SloperPlanCategory.objects.get(category_title="Hospital")
    plan_basic_price = SloperBasicPrice.objects.get(category_id = plan_category.id)
    price_per_patient = plan_basic_price.price
    if not hospital_plan_id == "0":
        sloper_plan = SloperPlan.objects.get(id=hospital_plan_id)
        total_price = float(price_per_patient * patient_count)
        discount = float(sloper_plan.data["off"]) 
        total_subscription_amount = total_price * (100 - discount) / 100
        original_price = total_price
        discount_price = total_price - total_subscription_amount
    else:
        total_price = float(price_per_patient * 10)
        original_price = 0
        discount_price = 0
        total_subscription_amount = total_price
        discount = 0
    request.session['sloper_hospital_session_data'] = {
        "plan_data":{
            "total_price":total_price,
            "patient_count":patient_count,
            "original_price":original_price,
            "discount_price": discount_price,
            "total_subscription_amount": total_subscription_amount,
            "discount":discount,
        }
            }
    request.session.modified = True
    return JsonResponse({"success": True})


def summery_sloper_hospital_plan(request, hospital_name, slug):
    sloper_hospital_session = request.session["sloper_hospital_session_data"]
    sloper_hospital_session_data = sloper_hospital_session["plan_data"]
    if request.method == "POST":
        selected_hospital_id = SloperHospital.objects.get(slug = slug).id
        sloper_hospital_session["plan_data"]["selected_hospital_id"] = selected_hospital_id
        request.session.modified = True
        return redirect('summery_sloper_hospital_plan', hospital_name, slug)
    else:
        hospital_id = sloper_hospital_session["plan_data"]["selected_hospital_id"]
        hospital_data = SloperHospital.objects.get(id=hospital_id)
        return render(request, "pages/sloper-subscription/hospital-plan-summery.html", {"sloper_hospital_session_data": sloper_hospital_session_data,
        "hospital_data": hospital_data})


def select_hospital_for_sloper_subscription(request):
    return render(request, "pages/sloper-subscription/select-hospital.html")    


def get_search_hospital_data(request):
    words = request.POST["words"]
    hospitals = SloperHospital.objects.filter(name__icontains = words, is_active = True)
    return render(request, "pages/sloper-subscription/search_results.html", {"hospitals":hospitals})
    

def add_plan_type_onetime_or_recurring(request):
    countries = WebCountry.objects.all()
    if request.method == "POST":
        one_time_or_recurring = request.POST["one_time_or_recurring"]
        sloper_hospital_session_data = request.session["sloper_hospital_session_data"]
        sloper_hospital_session_data["plan_data"]["one_time_or_recurring"] = one_time_or_recurring
        request.session.modified = True
    return render(request, "pages/sloper-subscription/sloper-hospital-billing-address.html", {"countries":countries})


def add_hospital_plan_address(request):
    if request.method == "POST":
        sloper_hospital_session_data = request.session["sloper_hospital_session_data"]
        plan_type = sloper_hospital_session_data["plan_data"]["one_time_or_recurring"]
        total_subscription_amount = sloper_hospital_session_data["plan_data"]["total_price"]
        total_amount_on_stripe = int(float(total_subscription_amount) * 100)

        line_items = [{
            'name': f"Sloper Subscription for Hospital",
            'currency': 'usd',
            'amount': total_amount_on_stripe,
            'quantity': 1,
        }]

        user_id = request.user.id
        user_subscription = UserSubscriptions.objects.get(user_id = user_id)
        customer_id = user_subscription.customer_id
        success_url = 'sloper-hospital-order-confirmation/'
        cancel_url = 'render-sloper-landing-page/'
        payment_sloper_subscription = payment_for_subscription(line_items=line_items, success_url=success_url, cancel_url=cancel_url, user_id = user_id, customer_id=customer_id, mode='payment')

        sloper_hospital_session_data['checkout_session_id'] = payment_sloper_subscription['id']
        sloper_hospital_session_data['payment_intent_id'] = payment_sloper_subscription['payment_intent']

        sloper_hospital_session_data["address"] = get_sloper_billing_address_from_post_request(request.POST)

        request.session.modified = True
        return JsonResponse({"success": True, "sessionId": payment_sloper_subscription['id']})


def sloper_hospital_order_confirmation(request):
    sloper_hospital_session_data = request.session["sloper_hospital_session_data"]
    
    address = sloper_hospital_session_data["address"]

    plan_data = sloper_hospital_session_data["plan_data"]

    hospital_id = plan_data["selected_hospital_id"]
    hospital_data = SloperHospital.objects.get(id=hospital_id)
    hospital_address = f"{hospital_data.street}, {hospital_data.city}, {hospital_data.state}, {hospital_data.country}, {hospital_data.zipcode}"

    total_amount = plan_data["total_price"]
    total_amount_on_stripe = int(float(total_amount) * 100)
    discount = plan_data["discount"]
    original_price = float(total_amount_on_stripe) / (1 - (float(discount) / 100))
    discount_price = original_price - float(total_amount_on_stripe)

    user_id = request.user.id
    user_subscription = UserSubscriptions.objects.get(user_id=user_id)
    customer_id = user_subscription.customer_id

    sloper_stripe_data = SloperStripeData()
    sloper_stripe_data.email = request.user.email.lower()
    sloper_stripe_data.customer_id=customer_id

    if plan_data["one_time_or_recurring"] == "RECURRING":
        is_recurring = True

        plan_name = "Hospital Plan"
        description = "Sloper Hospital Subscription"
        stripe_product = create_product(plan_name, description)

        recurring = {"interval": "month", "interval_count": 1}
        stripe_subscription_price = create_subscription_price(amount=total_amount_on_stripe, recurring=recurring, stripe_product_id=stripe_product["id"])

        date_after_one_month = int(get_unix_timestamp_of_one_month_later())
        subscription_schedule = create_subscription_schedule(customer_id=customer_id, start_date=date_after_one_month, price_id=stripe_subscription_price["id"])

        sloper_stripe_data.stripe_product_id = stripe_product["id"]
        sloper_stripe_data.stripe_price_id = stripe_subscription_price["id"]
        sloper_stripe_data.schedule_subscription_id = subscription_schedule["id"]
    else:
        is_recurring = False

    payment_intent_id = sloper_hospital_session_data['payment_intent_id']
    stripe_data = get_stripe_data_for_sloper_subscription(payment_intent_id)

    sloper_stripe_data.reciept_url = stripe_data['receipt_url']
    sloper_stripe_data.stripe_data = stripe_data['stripe_data']
    sloper_stripe_data.save()

    sloper_billing_address = create_sloper_billing_address(address)

    user_sloper_subscription = UserSloperSubscription.objects.create(
        category="Hospital",
        sloper_stripe_data_id=sloper_stripe_data.id,
        plan_detail={
            "discount": plan_data["discount"],
            "price": plan_data["total_price"],
            "user_count": plan_data["patient_count"],
            "original_price": original_price,
            "discount_price": discount_price
        },
        is_recurring=is_recurring,
        billing_address_id=sloper_billing_address.id,
    )

    UserGiftSloperPlan.objects.create(
        sender_user_id=request.user.id,
        receiver_email=hospital_data.management_email.lower(),
        user_detail={
            "hospital_name": hospital_data.name,
            "management_name": hospital_data.management_name,
            "hospital_address": hospital_address,
            "phone_number": hospital_data.phone_number
        },
        is_wasted=False,
        user_sloper_subscription_id=user_sloper_subscription.id
    )

    return render(request, "pages/sloper-subscription/sloper-hospital-order-confirmation.html")

def sloper_hospital_order_details(request):
    sloper_hospital_session_data = request.session["sloper_hospital_session_data"]
    plan_details = sloper_hospital_session_data["plan_data"]
    address = sloper_hospital_session_data["address"]
    selected_hospital_id = plan_details["selected_hospital_id"] 
    hospital_details = SloperHospital.objects.get(id=selected_hospital_id)
    return render(request, "pages/sloper-subscription/sloper-hospital-order-detail.html", {"hospital_details": hospital_details, "plan_details": plan_details,
    "address": address})    
    



def pay_school_subscription(request):
    no_of_month = int(request.POST['no_of_month'])
    no_of_student = int(request.POST['no_of_student'])
    no_of_teacher = int(request.POST['no_of_teacher'])
    plan_name = f"{no_of_student}_student_{no_of_teacher}_teacher_{no_of_month}_month"
    description = "school plan"
    student_price = SloperBasicPrice.objects.get(name = "Price Per Student").price
    teacher_price = SloperBasicPrice.objects.get(name = "Price Per Teacher").price
    discount = SloperBasicPrice.objects.get(name = "Discount on School Plan").price
    original_price = (no_of_student * student_price) + (no_of_teacher * teacher_price) * no_of_month
    price_after_discount = round(original_price - (original_price * discount / 100), 2) 
    total_discount = original_price - price_after_discount 
    # stripe_product = create_product(plan_name, description)
    if 'sloper_school_plan_data' in request.session:
        del request.session['sloper_school_plan_data']
    request.session['sloper_school_plan_data'] = {}  # Initialize the dictionary
    request.session['sloper_school_plan_data']['plan_data'] = {
        "no_of_month": no_of_month,
        "no_of_student": no_of_student,
        "no_of_teacher": no_of_teacher,
        "student_price": int(student_price),
        "teacher_price": int(teacher_price),
        "original_price": float(original_price),
        "price_after_discount":float(price_after_discount),
        "total_discount":float(total_discount),
        "discount_percentage": int(discount),
        "plan_name": plan_name,
        "description": description
    }
    return JsonResponse({"success": True})



def select_sloper_school(request):
    if request.method == "POST":
        search_word = request.POST.get("words")
        schools = SloperSchool.objects.filter(name__icontains = search_word, is_active = True)
        return render(request, "pages/sloper-subscription/search_results_school.html", {"schools":schools})
    return render(request, "pages/sloper-subscription/select-school.html" )  


def summery_sloper_school_plan(request, school_name, slug):
    sloper_school_session = request.session["sloper_school_plan_data"]
    sloper_school_session_data = sloper_school_session["plan_data"]
    if request.method == "POST":
        selected_school_id = SloperSchool.objects.get(slug = slug).id
        sloper_school_session["plan_data"]["selected_school_id"] = selected_school_id
        request.session.modified = True
        return redirect('summery_sloper_school_plan', school_name, slug)
    else:
        school_id = sloper_school_session["plan_data"]["selected_school_id"]
        school_data = SloperSchool.objects.get(id=school_id)
        return render(request, "pages/sloper-subscription/school-plan-summery.html", {"sloper_school_session_data": sloper_school_session_data,
        "school_data": school_data})     


def add_school_plan_type_onetime_or_recurring(request):
    countries = WebCountry.objects.all()
    if request.method == "POST":
        one_time_or_recurring = request.POST["one_time_or_recurring"]
        sloper_school_session_data = request.session["sloper_school_plan_data"]
        sloper_school_session_data["plan_data"]["one_time_or_recurring"] = one_time_or_recurring
        request.session.modified = True
        return render(request, "pages/sloper-subscription/sloper-school-billing-address.html", {"countries":countries})
    return render(request, "pages/sloper-subscription/sloper-school-billing-address.html", {"countries":countries})


def add_school_plan_address(request):
    if request.method == "POST":
        sloper_school_session_data = request.session["sloper_school_plan_data"]
        plan_type = sloper_school_session_data["plan_data"]["one_time_or_recurring"]
        total_subscription_amount = sloper_school_session_data["plan_data"]["price_after_discount"]
        total_amount_on_stripe = int(float(total_subscription_amount) * 100)
        line_items = [{
            'name': f"Sloper Subscription for school",
            'currency': 'usd',
            'amount': total_amount_on_stripe,
            'quantity': 1,
        }]

        user_id = request.user.id
        user_subscription = UserSubscriptions.objects.get(user_id = user_id)
        customer_id = user_subscription.customer_id
        success_url = 'sloper-school-order-confirmation/'
        cancel_url = 'render-sloper-landing-page/'
        # payment_sloper_subscription = payment_for_subscription(line_items=line_items, success_url=success_url, cancel_url=cancel_url, user_id = user_id, customer_id=customer_id, mode='payment')

        # sloper_school_session_data['checkout_session_id'] = payment_sloper_subscription['id']
        # sloper_school_session_data['payment_intent_id'] = payment_sloper_subscription['payment_intent']

        sloper_school_session_data["address"] = get_sloper_billing_address_from_post_request(request.POST)
        request.session.modified = True
        return JsonResponse({"success": True, "sessionId": "3453454"})   


def sloper_school_order_confirmation(request):
    sloper_school_plan_data = request.session["sloper_school_plan_data"]
    address = sloper_school_plan_data["address"]
    plan_data = sloper_school_plan_data["plan_data"]
    school_id = plan_data["selected_school_id"]
    school_data = SloperSchool.objects.get(id=school_id)
    school_address = f"{school_data.street}, {school_data.city}, {school_data.state}, {school_data.country}, {school_data.zipcode}"
    total_amount = plan_data["price_after_discount"]
    total_amount_on_stripe = int(float(total_amount) * 100)
    discount = plan_data["discount_percentage"]
    original_price = float(total_amount_on_stripe) / (1 - (float(discount) / 100))
    discount_price = original_price - float(total_amount_on_stripe)
    user_id = request.user.id
    user_subscription = UserSubscriptions.objects.get(user_id=user_id)
    customer_id = user_subscription.customer_id
    sloper_stripe_data = SloperStripeData()
    sloper_stripe_data.email = request.user.email.lower()
    sloper_stripe_data.customer_id=customer_id

    if plan_data["one_time_or_recurring"] == "RECURRING":
        is_recurring = True
        plan_name = "School Plan"
        description = "Sloper School Subscription"
        stripe_product = create_product(plan_name, description)
        recurring = {"interval": "month", "interval_count": 1}
        stripe_subscription_price = create_subscription_price(amount=total_amount_on_stripe, recurring=recurring, stripe_product_id=stripe_product["id"])
        date_after_one_month = int(get_unix_timestamp_of_one_month_later())
        subscription_schedule = create_subscription_schedule(customer_id=customer_id, start_date=date_after_one_month, price_id=stripe_subscription_price["id"])
        sloper_stripe_data.stripe_product_id = stripe_product["id"]
        sloper_stripe_data.stripe_price_id = stripe_subscription_price["id"]
        sloper_stripe_data.schedule_subscription_id = subscription_schedule["id"]
    else:
        is_recurring = False

    payment_intent_id = sloper_school_plan_data['payment_intent_id']
    stripe_data = get_stripe_data_for_sloper_subscription(payment_intent_id)
    sloper_stripe_data.reciept_url = stripe_data['receipt_url']
    sloper_stripe_data.stripe_data = stripe_data['stripe_data']
    sloper_stripe_data.save()
    sloper_billing_address = create_sloper_billing_address(address)
    user_sloper_subscription = UserSloperSubscription.objects.create(
                                                                    category="school",
                                                                    sloper_stripe_data_id=sloper_stripe_data.id,
                                                                    plan_detail={
                                                                                "discount": plan_data["discount"],
                                                                                "price": plan_data["total_price"],
                                                                                "user_count": plan_data["patient_count"],
                                                                                "original_price": original_price,
                                                                                "discount_price": discount_price
                                                                                },
                                                                    is_recurring=is_recurring,
                                                                    billing_address_id=sloper_billing_address.id,
                                                                    )

    UserGiftSloperPlan.objects.create(
                                     sender_user_id=request.user.id,
                                     receiver_email=school_data.management_email.lower(),
                                     user_detail={
                                                 "school_name": school_data.name,
                                                 "management_name": school_data.management_name,
                                                 "school_address": school_address,
                                                 "phone_number": school_data.phone_number
                                                 },
                                     is_wasted=False,
                                     user_sloper_subscription_id=user_sloper_subscription.id
                                     )
    return render(request, "pages/sloper-subscription/sloper-school-order-confirmation.html")

def sloper_school_order_details(request):
    sloper_school_plan_data = request.session["sloper_school_plan_data"]
    plan_details = sloper_school_plan_data["plan_data"]
    address = sloper_school_plan_data["address"]
    selected_school_id = plan_details["selected_school_id"] 
    school_details = SloperSchool.objects.get(id=selected_school_id)
    return render(request, "pages/sloper-subscription/sloper-school-order-detail.html", {"school_details": school_details, "plan_details": plan_details,
    "address": address})


# stripe call this webhook when schedule subscription started
# this webhook is to get sloper subscription which is just started
@csrf_exempt
def stripe_webhook_for_schedule_subscription(request):
    endpoint_secret = 'whsec_6ba36c64e14bad1a7391e0fa23e825e2f182345510286a280d3e3be009045a7a'
    event = None
    payload = request.body
    sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        customer_id = event['data']['object']['customer'] 
        subscription_id = event['data']['object']['subscription']
        sloper_stripe_data = SloperStripeData.objects.get(customer_id=customer_id)
        sloper_stripe_data.subscription_id = subscription_id
        sloper_stripe_data.save()
        return JsonResponse({'success': True, 'message': 'Subscription Started'})
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e
    except:
        return JsonResponse({'success': False, 'message': 'Something Went Wrong'})

@login_required
def activate_sloper_subscription(request, slug):
    time = timezone.now()
    user_id = request.user.id     
    if not UserSloperSubscription.objects.filter(user_id = user_id, is_active=True).exists():
        subscription_id = request.POST['subscription_id']
        subscription_data = UserGiftSloperPlan.objects.get(id=subscription_id)
        subscription_data = UserSloperSubscription.objects.get(id=subscription_data.user_sloper_subscription_id)
        stripe_data = SloperStripeData.objects.get(id=subscription_data.sloper_stripe_data_id)
        if subscription_data.user_sloper_plan.is_recurring:
            customer_id = stripe_data.customer_id
            start_date = datetime.now()

            price_id = stripe_data.stripe_price_id
            subscription_schedule = create_subscription_schedule(customer_id, start_date, price_id)
            print(subscription_schedule, '-0-0-0-0-0-0--0-0---')
            # subscription_data.user_id = user_id
            # subscription_data.is_active = True
            # subscription_data.start_at = time
            # subscription_data.save()
            pass
        else:
            subscription_data.user_id = user_id
            subscription_data.is_active = True
            subscription_data.start_at = time
            subscription_data.save()
            pass
        return JsonResponse({'success': True, 'message': 'Plan Activated'})
    else:
        return JsonResponse({'success': False, 'message': 'You have already active plan'})


def cancel_sloper_subscription(request, slug):
    try:
        subscription_data = UserSloperSubscription.objects.get(slug=slug, is_canceled=False, is_ended=False)
        stripe_subscription_id = subscription_data.sloper_stripe_data.subscription_id
        cancel_stripe_subscription(stripe_subscription_id)
        subscription_data.is_canceled = True
        subscription_data.is_active = False
        time = timezone.now()
        subscription_data.canceled_at = time
        subscription_data.save()
        messages.success(request, "Plan Canceled")
        return redirect('my_sloper_subscription')
    except UserSloperSubscription.DoesNotExist:
        messages.error(request, "No Active Subscription")
        return redirect('my_sloper_subscription')
    except:
        messages.error(request, "Failed to Cancel Sloper Subscription")
        return redirect('my_sloper_subscription')

    


def registered_user_reciept(request, encrptyed_order_id):
    try:
        order_id = text_decryption(encrptyed_order_id)
        product_order = ProductOrder.objects.get(order_id=order_id)
        product_data = ProductOrderData.objects.filter(product_order_id = product_order.id)
        product_images = []
        for product in product_data:
            images = ShopProductImage.objects.get(shop_product_id = product.shop_product_id)
            product_images.append(images)
        original_price = []
        offer_price = []
        quantity = []
        for order in product_data:
            count = order.quantity
            quantity.append(count)
            original = float(order.shop_product.original_price * order.quantity)
            original_price.append(original)
            offer = float(order.per_unit_price * order.quantity)
            offer_price.append(offer)

        product_original_price =sum(original_price)
        product_offer_price = sum(offer_price)
        if product_order.offer_id:
            offer_data = Offer.objects.get(id = product_order.offer_id)
            price_after_offer = (product_offer_price * offer_data.percentage)/100
            total_savings = product_original_price - price_after_offer
        else:
            offer_data = None
            total_savings = product_original_price - product_offer_price
            price_after_offer = None
        
        return render(request, "email_html/registered-user-receipt.html", {"product_offer_price":product_offer_price,
                                                                "product_original_price":product_original_price,
                                                                "original_price":original_price,
                                                                "offer_price":offer_price,
                                                                "total_savings":total_savings,
                                                                "product_order": product_order,
                                                                "product_data": product_data,
                                                                "total_quantity": sum(quantity),
                                                                "product_images": product_images
                                                                })
    except:
        messages.error(request, 'Something Went Wrong')
        return redirect('home') 

def guest_user_reciept(request, encrptyed_order_id):
    try:
        order_id = text_decryption(encrptyed_order_id)
        product_order = GuestUserData.objects.get(order_id=order_id)
        product_data = []
        product_count = 0
        product_offer_price = 0
        product_original_price = 0
        for product in product_order.order_detail:
            product_count += 1
            shop_product = ShopProduct.objects.get(id = product.get("id"))
            product_original_price += shop_product.original_price
            product_offer_price += shop_product.offer_price
            quantity = product.get("quantity")
            product_dict = {"product": shop_product, "quantity": quantity}
            product_data.append(product_dict)
        total_savings = product_original_price - product_offer_price
        product_images = []
        for data in product_data:
            images = ShopProductImage.objects.get(shop_product_id = data.get("product").id)
            product_images.append(images)
        
        return render(request, "email_html/guest-user-receipt.html", {  "total_savings":total_savings,
                                                                        "product_order": product_order,
                                                                        "product_data": product_data,
                                                                        "product_count": product_count,
                                                                        "product_images": product_images,
                                                                        "product_original_price": product_original_price,
                                                                        "product_offer_price": product_offer_price
                                                                    })
    except:
        messages.error(request, 'Something Went Wrong')
        return redirect('home')

def cancel_order_refund(request, product_order) -> dict:
    try:
        if product_order.order_status == 'Canceled' and product_order.is_refunded:
            return {'status': False,'message': 'Order Already Cancelled and Refund is Initiated'}

        user = request.user
        if float(product_order.paid_by_stripe) > 0:
            order_detail = OrderDetail.objects.filter(product_order_id__order_id=product_order.order_id, user_id=user.id).last()

            if not order_detail:
                return {'status': False,'message': 'Order Detail Not Exist'}

            try:
                refund_response = create_refund(order_detail.stripe_charge_id, int(float(product_order.paid_by_stripe) * 100))
            except:
                return {'status': False,'message': 'Order Alreay Cancelled'}
            
            if refund_response.get("status") != "succeeded":
                return {'status': False,'message': 'Not Able to Cancel Your Order'}

        if float(product_order.paid_by_wallet) > 0:
            user.wallet = float(user.wallet) + float(product_order.paid_by_wallet)
            user.save()

        product_order.is_refunded = True
        product_order.order_status = "Canceled"
        product_order.canceled_by = "Customer"
        product_order.canceled_at = datetime.now()
        product_order.save()
        return {'status': True, 'message': 'Order Cancelled And Amount Refunded to Your Account/Wallet'}
    except:
        return {'status': False,'message': 'Something Went Wrong'}

def rss_feed(request):
    with open('rss.xml') as f:
        data = f.read()
    return HttpResponse(data, content_type='application/xml')


def sloper_coming_soon(request):
    return render(request, 'sloper-coming-soon.html')

# to take data backpup by giving model name
# import os
# import subprocess
# from django.apps import apps
# from django.conf import settings
# from django.http import JsonResponse

# def backup_model(app_label, model_name):
#     i = 0
#     path_list = []
#     db_host = settings.DATABASES.get('default').get('HOST')
#     db_user = settings.DATABASES.get('default').get('USER')
#     db_name = settings.DATABASES.get('default').get('NAME')
#     file_path = settings.BASE_DIR
#     for model in model_name:
#         new_path = f"{file_path}/backup/test/file{i}.sql"
#         path_list.append(new_path)
#         model = apps.get_model(app_label, model)
#         table_name = model._meta.db_table
#         subprocess.run(["pg_dump", "-h", db_host, "-U", db_user, "-d", db_name, "-t", table_name, "-f", new_path])
#         i+=1
#     return JsonResponse({'files': path_list}, safe=False)

# def restore_model(request):
#     db_host = settings.DATABASES.get('default').get('HOST')
#     db_user = settings.DATABASES.get('default').get('USER')
#     db_name = settings.DATABASES.get('default').get('NAME')
#     folder_path = os.path.join(settings.BASE_DIR, 'backup')

#     for i, model_name in enumerate(get_model_list_for_sloper()):
#         file_path = os.path.join(folder_path, f'test/file{i}.sql')
#         model = apps.get_model("adminpanel", model_name)
#         table_name = model._meta.db_table
#         command = f"psql -h {db_host} -U {db_user} -d {db_name} < {file_path}"
#         result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            

# def get_model_list_for_sloper():
#     return ["SloperPlanCategory", "SloperBasicPrice", "SloperPlan", "SloperStripeData", "SloperBillingAddress", "UserSloperSubscription", "UserGiftSloperPlan", "SloperHospital", "HospitalRegisteredPatients", "HospitalUnregisteredPatients", "UserSchoolPlan"]

# def take_model(request):
#     models_list = get_model_list_for_sloper()
#     backup_model("adminpanel", models_list)

#FUNDRAISING VIEWS:

def start_fundraising_page(request):
    return render(request,'pages/start_fundraising_landing_page.html')






