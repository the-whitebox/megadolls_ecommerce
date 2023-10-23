from django.utils.text import slugify
from web_app.payment import create_customer
import ast
import re
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q, Sum, F, FloatField
from django.db.models.functions import TruncMonth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.exceptions import EmptyResultSet
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.contrib import messages
from web_app.views import mobile_update
from .choices import USER_TYPE
from .serializers import *
from .models import *
import random
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.conf import settings
import calendar
from .helper import *
from web_app.payment import *
from .global_dict import interval_dict
from web_app.payment import *
from web_app.twilio import *
from django.utils.html import strip_tags
from .email import *
from django.db.models.aggregates import Max
import json
from .reports import generate_pdf_report, generate_csv_report
import traceback
import logging 
from django.db.models import Prefetch
logging.getLogger().setLevel(logging.DEBUG)
# redirect links
redirect_url = "/adminpanel/login"
empty_fields = "Please Fill All Fields"

# email template
mail_credentail = 1
template_forget_password = 2

# product management
category_template = "product_management/category/"
subcategory_template = "product_management/subcategory/"
dress_type_template = "product_management/dress_type/"
collection_template = "product_management/collection/"
color_template = "product_management/color/"


def is_normal_user(request):
    return request.user.is_authenticated and request.user.user_type == "CUSTOMER"


def login_user(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        # check authenticate user
        email = request.POST.get("email").lower()
        password = request.POST.get("password")
        
        user = authenticate(email=email, password=password, is_delete=False)

        if user is not None:
            # authenticated user
            login(request, user)
            return redirect("dashboard")

        else:
            messages.error(request, "Wrong Credential")
            return redirect("login")

    return render(request, "login.html")


def logout_user(request):
    logout(request)
    return redirect("login")

# to reset password with otp sent on email
def forget_password(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        try:
            email = request.POST.get("email").lower()
            # url = reverse(reset_password)
            password = random.randint(100000, 999999)

            try:
                user = User.objects.get(email=email)
            except:
                messages.error(request, "User Not Found")

            name = user.name
            user.set_password(str(password))
            user.save()
            forgot_password(email, password)
            
            User.objects.filter(email=email, is_active=True).update(is_mail_send=True)
            messages.success(
                request, "New Password is Sent to Your Email"
            )

            return redirect("login")

        except Exception as err:
            messages.error(request, "Failed to Send Mail")

    return render(request, "forget_password.html")


@login_required(login_url="login")
def get_sidebar_dropdown(request):
    module = Module.objects.filter(is_active=True)
    sub_module = SubModule.objects.filter(is_active=True, module__is_active=True)


@login_required(login_url="login")
def dashboard(request):
    if is_normal_user(request):
        return redirect("web_login")

    total_customer_count = User.objects.filter(user_type="CUSTOMER").count()
    total_sub_admin_count = User.objects.filter(user_type="SUBADMIN").count()
    customer_count = (
        User.objects.annotate(month=TruncMonth("created"))
        .values("month")
        .annotate(c=Count("id"))
        .filter(user_type="CUSTOMER")
    )
    customer_data = []

    # monthly_sales = (
    #     ProductOrderData.objects.annotate(month=TruncMonth("product_order__order_at"))
    #     .values("month")
    #     .annotate(monthly_sale = Sum(
    #         F("quantity") * F("per_unit_price"),
    #         output_field=FloatField()
    #     ),product_order_id=Count("product_order_id")).order_by("month")
    # )
    sales_data = []
    product_order = ProductOrder.objects.all().prefetch_related('productorderdata_set')
    monthly_sales = (product_order.annotate(month=TruncMonth("order_at")).values("month").annotate(monthly_sale = Sum(
            F("productorderdata__quantity") * F("productorderdata__per_unit_price"),
            output_field=FloatField()
        )).exclude(monthly_sale=None).order_by("month"))

    i = 0
    while i <= 11:
        i += 1
        obj = dict()
        sale_obj = dict()
        obj.update({"CUSTOMER": 0, "month": calendar.month_name[i]})
        sale_obj.update({"SALE": 0, "month": calendar.month_name[i]})
        customer_data.append(obj)
        sales_data.append(sale_obj)

    for i in customer_count:
        customer_data[int(i["month"].strftime("%m")) - 1]["CUSTOMER"] = i["c"]

    for i in monthly_sales:
        sales_data[int(i["month"].strftime("%m")) - 1]["SALE"] = i["monthly_sale"]
 
    total_blog_subscribers = BlogSubscriber.objects.all().count()
    total_shero_subscribers = UserSubscriptions.objects.exclude(shero_subscription__isnull=True).count()  

    total_blogs = Blog.objects.all().count()

    dolls_out_of_stock = ShopProduct.objects.filter(quantity=0, is_delete=False, subcategory__id=1).count()
    doll_sets_out_of_stock = ShopProduct.objects.filter(quantity=0, is_delete=False, subcategory__id=2).count()
    dress_sets_out_of_stock = ShopProduct.objects.filter(quantity=0, is_delete=False, subcategory__id=3).count()
    # total_out_of_imagine_products = ImagineProduct.objects.filter(quantity=0).count()

    total_shop_products_count = ShopProduct.objects.filter(is_delete=False).count()
    total_imagine_products_count = ImagineProduct.objects.filter(is_delete=False).count()

    total_products_count = total_shop_products_count + total_imagine_products_count



    total_dolls_count = ShopProduct.objects.filter(subcategory__id=1, is_delete=False).aggregate(Sum('quantity'))['quantity__sum']
    total_doll_sets_count = ShopProduct.objects.filter(subcategory__id=2, is_delete=False).aggregate(Sum('quantity'))['quantity__sum']
    total_dress_sets_count = ShopProduct.objects.filter(subcategory__id=3, is_delete=False).aggregate(Sum('quantity'))['quantity__sum']
    total_create_count = ImagineProduct.objects.filter(subcategory__id=4, is_delete=False).count()
    total_play_count = ImagineProduct.objects.filter(subcategory__id=5, is_delete=False).count()

    orders = ProductOrder.objects.all()
    total_amount = orders.aggregate(total_amount = Sum("total_amount"))
    total_order_revenue = float(total_amount.get("total_amount", 0) if total_amount.get("total_amount", 0) else 0)

    completed_orders = ProductOrder.objects.filter(order_status = "Completed").count() 
    accepted_orders = ProductOrder.objects.filter(order_status = "Accepted").count()
    shipped_orders = ProductOrder.objects.filter(order_status = "Shipped").count()
    canceled_orders = ProductOrder.objects.filter(order_status = "Canceled").count()
    # customers_order = ProductOrder.objects.filter(order_status__isnull=True).count()
    total_orders = ProductOrder.objects.all().count()

    subscription_plans = SubscriptionPlan.objects.filter(is_active = True)
    shero_subscribers_count = UserSubscriptions.objects.filter(subscription_id__isnull=False).values("shero_subscription_id").annotate(subscriber_count = Count("shero_subscription_id"))
    
    shero_monthly_total = 0
    shero_quarterly_total = 0
    shero_bi_annual_total = 0
    shero_annual_total = 0
    
    if subscription_plans:
        monthly_plan = subscription_plans.filter(plan_type='Monthly')
        quarterly_plan = subscription_plans.filter(plan_type='Quarterly')
        bi_annual_plan = subscription_plans.filter(plan_type='Bi-Annual')
        annual_plan = subscription_plans.filter(plan_type='Annual')
        
        for subscriber in shero_subscribers_count:
            if monthly_plan.exists() and monthly_plan[0].id == subscriber.get('shero_subscriber_id'):
                shero_monthly_total = monthly_plan.original_price * subscriber.get('subscriber_count')
            elif quarterly_plan.exists() and quarterly_plan[0].id == subscriber.get('shero_subscriber_id'):
                shero_quarterly_total = quarterly_plan.original_price * subscriber.get('subscriber_count')
            elif bi_annual_plan.exists() and bi_annual_plan[0].id == subscriber.get('shero_subscriber_id'):
                shero_bi_annual_total = bi_annual_plan.original_price * subscriber.get('subscriber_count')
            elif annual_plan.exists() and annual_plan[0].id == subscriber.get('shero_subscriber_id'):
                shero_annual_total = annual_plan.original_price * subscriber.get('subscriber_count')
    
    total_subscription_revenue = shero_monthly_total + shero_quarterly_total + shero_bi_annual_total + shero_annual_total

    # guest_order_revenue = float(GuestUserData.objects.all().aggregate(total_amount = Sum("total_amount"))['total_amount'])
    # guest_order_revenue = float(total_amount_aggregate['total_amount']) if total_amount_aggregate['total_amount'] is not None else 0.0
    total_amount_aggregate = GuestUserData.objects.aggregate(total_amount=Sum("total_amount"))
    guest_order_revenue = float(total_amount_aggregate['total_amount']) if total_amount_aggregate['total_amount'] is not None else 0.0
    total_revenue_order = total_order_revenue + total_subscription_revenue + guest_order_revenue
    total_revenue = round(total_revenue_order, 2)
                
    shero_dolls = SheroDolls.objects.filter(is_active = True).count()
    shero_subscription_plan = subscription_plans.count()
    
    user_referral = UserReferral.objects.all().count() 

    m_check = ModulePermission.objects.filter(user_id=request.user.id)
    
    return render(
        request,
        "dashboard.html",
        {   
            "user_referral": user_referral if user_referral else 0,
            "shero_subscription_plan": shero_subscription_plan if shero_subscription_plan else 0,
            "shero_dolls": shero_dolls if shero_dolls else 0,
            "total_orders": total_orders if total_orders else 0,
            "total_order_revenue": total_order_revenue if total_order_revenue else 0,
            "total_revenue": total_revenue if total_revenue else 0,
            "shero_monthly_total": shero_monthly_total if shero_monthly_total else 0,
            "shero_quarterly_total": shero_quarterly_total if shero_quarterly_total else 0,
            "shero_bi_annual_total": shero_bi_annual_total if shero_bi_annual_total else 0,
            "shero_annual_total": shero_annual_total if shero_annual_total else 0,
            "total_subscription_revenue": total_subscription_revenue if total_subscription_revenue else 0,
            # "customers_order": customers_order if customers_order else 0,
            "completed_orders": completed_orders if completed_orders else 0,
            "accepted_orders": accepted_orders if completed_orders else 0,
            "shipped_orders": shipped_orders if shipped_orders else 0,
            "canceled_orders": canceled_orders if canceled_orders else 0,
            "dolls_out_of_stock": dolls_out_of_stock if dolls_out_of_stock else 0,
            "doll_sets_out_of_stock": doll_sets_out_of_stock if doll_sets_out_of_stock else 0,
            "dress_sets_out_of_stock": dress_sets_out_of_stock if dress_sets_out_of_stock else 0,
            "total_play_count": total_play_count if total_play_count else 0,
            "total_create_count": total_create_count if total_create_count else 0,
            "total_dress_sets_count": total_dress_sets_count if total_dress_sets_count else 0,
            "total_doll_sets_count": total_doll_sets_count if total_doll_sets_count else 0,
            "total_dolls_count": total_dolls_count if total_dolls_count else 0,
            "total_shop_products_count": total_shop_products_count if total_shop_products_count else 0,
            "total_imagine_products_count": total_imagine_products_count if total_imagine_products_count else 0,
            "total_products_count": total_products_count if total_products_count else 0,
            "total_customer_count": total_customer_count if total_customer_count else 0,
            "total_sub_admin_count": total_sub_admin_count if total_sub_admin_count else 0,
            "customer_count": customer_data,
            "monthly_sale": sales_data,
            "total_blogs": total_blogs if total_blogs else 0,
            "total_blog_subscribers": total_blog_subscribers if total_blog_subscribers else 0,
            "total_shero_subscribers": total_shero_subscribers if total_shero_subscribers else 0,
            "m_check": m_check,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )



@login_required(login_url="login")
def user_profile(request):
    if is_normal_user(request):
        return redirect("web_login")

    email = request.user

    user = User.objects.get(email=email, is_active=True)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "profile.html",
        {
            "user": user,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def update_user_profile(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        post = request.POST
        name = post.get("name")
        new_mobile = post.get("mobile")
        country_code = request.POST.get("country_code")
        mobile = f"{country_code}{new_mobile}" 
        email = post.get("email").lower()
        profile_img = request.FILES.get("profile_img")
        try:
            user = User.objects.get(email=request.user)
            user.name = name
            user.mobile = mobile
            user.email = email
            if profile_img:
                user.profile_img = profile_img
            user.save()
            messages.success(request, "Profile Updated")

        except Exception as err:
            messages.error(request, "Update Failed")

    return redirect("profile")


@login_required(login_url="login")
def change_password(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        post = request.POST
        password = post.get("password")
        new_password = post.get("new_password")

        try:
            user = User.objects.get(email=request.user)

            if user.check_password(password):
                user.password = make_password(str(new_password))
                user.save()
                messages.success(request, "Password Changed")

            else:
                messages.error(request, "Password Does Not Match")

        except Exception as err:
            messages.error(request, "Password Change Failed")

    return redirect("profile")


@login_required(login_url="login")
def add_email_template(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("editor")
        email_template = EmailTemplate.objects.create(title=title, content=content)
        return redirect("view_email_templates")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "email_template_management/add.html",
         { 
        "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request),
        }

    )

def view_message_template(request):
    templates = MessageTemplate.objects.all()
    return render(request, "message_template_management/view.html", {'templates': templates,"m": permission(request),
        "module_list": helper(request),
        "m_check": per(request)})

def add_message_template(request):
    if request.method == "POST":
        title = request.POST.get("title")
        subject = request.POST.get("subject")
        content = request.POST.get("editor")
        MessageTemplate.objects.create(title=title, subject=subject, content=content)
        messages.success(request, "Added")
        return redirect("view_message_template")
    return render(request, "message_template_management/add.html",{"m": permission(request),
        "module_list": helper(request),
        "m_check": per(request)} )    


def edit_message_template(request, id):
    templates = MessageTemplate.objects.get(id = id)
    if request.method == "POST":
        subject = request.POST.get('subject')
        content = request.POST.get('editor')
        templates.subject = subject
        templates.content = content
        templates.save()
        messages.success(request, "Edited")
        return redirect('view_message_template')


    return render(request, "message_template_management/edit.html", {'template': templates,"m": permission(request),
        "module_list": helper(request),
        "m_check": per(request)})

@login_required(login_url="login")
def edit_email_template(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    temp_id = id
    mail_template = EmailTemplate.objects.get(id=temp_id, is_active=True)

    if request.method == "POST":
        subject = request.POST.get("subject")
        content = request.POST.get("editor")
        mail_template.subject = subject
        mail_template.content = content
        mail_template.save()
        return redirect("view_email_templates")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "email_template_management/edit.html",
        {
            "template": mail_template,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_email_templates(request):
    if is_normal_user(request):
        return redirect("web_login")

    templates = EmailTemplate.objects.all().order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "email_template_management/view.html",
        {
            "templates": templates,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_category(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = category_template + "add.html"

    if request.method == "POST":
        try:
            name = request.POST.get("categoryName")

            if not (name and not name.isspace()):
                raise ValueError(empty_fields)

            if Category.objects.filter(name=name).exists():
                messages.error(request, "Category Already Exist")
                return redirect("add_category")

            Category.objects.create(name=name)
            messages.success(request, "Category Added")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("add_category")

        except:
            messages.error(request, "Category Already Exists")

        return redirect("view_categories")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
            "model": model,
        },
    )


@login_required(login_url="login")
def view_category(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = category_template + "view.html"
    categories = Category.objects.all()
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "categories": categories,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def update_category(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = category_template + "edit.html"
    category = Category.objects.get(id=id)
    if request.method == "POST":
        try:
            name = request.POST.get("categoryName")
            is_active = request.POST.get("is_active")

            if not (name and not name.isspace()):
                raise ValueError(empty_fields)

            category.name = name
            category.is_active = is_active
            category.save()

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("update_category")

        messages.success(request, "Category Updated")

        return redirect("view_categories")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "category": category,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_category(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("category")
        category = Category.objects.get(id=id)
        category.delete()
        messages.success(request, "Category Deleted")

    return redirect("view_categories")


class CategoryView(APIView):
    def get(self, request):
        if is_normal_user(request):
            return redirect("web_login")

        data = Category.objects.filter(is_active=True).order_by("id")
        serializer = CategorySerializer(data, many=True)
        return Response({"success": True, "payload": serializer.data})

    def post(self, request):
        if is_normal_user(request):
            return redirect("web_login")

        data = request.data
        serializer = CategorySerializer(data, many=True)
        return Response({"success": True, "payload": serializer.data})


@login_required(login_url="login")
def add_shop_product(request):
    if is_normal_user(request):
        return redirect("web_login")

    subcategories = SubCategory.objects.filter(is_active=True, category__name="Shop")
    collections = ProductCollection.objects.filter(is_active=True)
    countries = Country.objects.filter(is_active=True)

    if request.method == "POST":
        post = request.POST

        name = post.get("name")
        offer_price = post.get("offer_price")
        original_price = post.get("original_price")
        alt_text = post.get("alt_text")
        og_title = post.get("og_title")
        og_description = post.get("og_description")
        description = post.get("description")
        quantity = post.get("quantity")
        notes = post.get("editor")
        subcategory_id = post.get("subcategory")
        collection_id = post.get("collection")
        country_id = post.get("country")
        color = None #post.get("color")
        size = None #post.get("size")
        weight = post.get('weight') if post.get('weight') else 0.30
        primary_img = request.FILES.get("primary_image")
        og_img = request.FILES.get("og_image")
        images = request.FILES.getlist("product_images")
        product_country_title = post.get("product_country_title")
        description_title = post.get("description_title")
        country_title = post.get("country_title")

        try:
            slug = slugify(name)
            shop_product = ShopProduct.objects.create(
                name=name,
                slug=slug,
                offer_price=offer_price,
                original_price=original_price,
                alt_text=alt_text,
                og_title=og_title,
                og_description=og_description,
                description=description,
                quantity=quantity,
                notes=notes,
                subcategory_id=subcategory_id,
                product_collection_id=collection_id,
                country_id=country_id,
                color=color,
                size=size,
                weight=weight,
                product_country_title=product_country_title,
                description_title=description_title,
                country_title=country_title
            )

            shop_product_image = ShopProductImage.objects.create(
                shop_product_id=shop_product.id, primary_img=primary_img, og_img=og_img
            )

            for i in range(0, len(images)):
                ShopProductImageSubTable.objects.create(
                    shop_product_image_id=shop_product_image.id, images=images[i]
                )
            messages.success(request, "Added Shop Product")

        except:
            messages.error(request, "Failed To Add Product")
        return redirect("view_shop_products")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/shop/add.html",
        {
            "subcategories": subcategories,
            "collections": collections,
            "countries": countries,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_shop_product(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    shop_product = ShopProduct.objects.get(id=id)
    shop_product_image = ShopProductImage.objects.get(shop_product_id=id)
    product_imgs = ShopProductImageSubTable.objects.filter(
        shop_product_image_id=shop_product_image.id
    )

    subcategories = SubCategory.objects.filter(is_active=True, category__name="Shop")
    collections = ProductCollection.objects.filter(is_active=True)
    countries = Country.objects.filter(is_active=True)

    if request.method == "POST":
        post = request.POST

        try:
            name = post.get("name")
            offer_price = post.get("offer_price")

            original_price = post.get("original_price")
            alt_text = post.get("alt_text")
            og_title = post.get("og_title")
            og_description = post.get("og_description")
            description = post.get("description")
            stock_status = post.get("stock_status")
            quantity = post.get('quantity')
            is_active = post.get("is_active")
            notes = post.get("editor")
            subcategory_id = post.get("subcategory")
            collection_id = post.get("collection")
            country_id = post.get("country")
            product_country_title = post.get("product_country_title")
            description_title = post.get("description_title")
            country_title = post.get("country_title")
            color = None#post.get("color")
            size = None#post.get("size")

            shop_product.name = name
            shop_product.slug = slugify(name)
            shop_product.offer_price = offer_price
            shop_product.original_price = original_price
            shop_product.alt_text = alt_text
            shop_product.og_title = og_title
            shop_product.og_description = og_description
            shop_product.description = description
            shop_product.stock_status = stock_status
            shop_product.quantity = quantity
            shop_product.is_active = is_active
            shop_product.notes = notes
            shop_product.subcategory_id = subcategory_id
            shop_product.product_collection_id = collection_id
            shop_product.country_id = country_id
            shop_product.color = color
            shop_product.size = size
            shop_product.product_country_title = product_country_title
            shop_product.description_title = description_title
            shop_product.country_title = country_title
            shop_product.save()

            primary_img = request.FILES.get("primary_image")
            og_img = request.FILES.get("og_image")
            images = request.FILES.getlist("product_images")

            if primary_img:
                shop_product_image.primary_img = primary_img

            if og_img:
                shop_product_image.og_img = og_img

            shop_product_image.save()

            i = 1
            j = 5 - product_imgs.count()
            for img in images:
                if i > j:
                    break
                ShopProductImageSubTable.objects.create(
                    images=img, shop_product_image_id=shop_product_image.id
                )
                i += 1

            messages.success(request, "Product Updated")
        except Exception as err:
            messages.error(request, "Update Failed")

        return redirect("view_shop_products")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/shop/edit.html",
        {
            "shop_product": shop_product,
            "shop_product_image": shop_product_image,
            "product_imgs": product_imgs,
            "subcategories": subcategories,
            "collections": collections,
            "countries": countries,
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@csrf_exempt
def delete_shop_product_image(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        product_image_id = request.POST.get("id")
        shop_product_image_sub_table = ShopProductImageSubTable.objects.filter(
            id=product_image_id
        )
        shop_product_image_sub_table.delete()

    return JsonResponse({"status": True}, safe=False)


@login_required(login_url="login")
def view_shop_products(request):
    if is_normal_user(request):
        return redirect("web_login")

    # shop_product_data = ShopProductImage.objects.filter(
    #     shop_product__is_delete=False
    # ).order_by("-id")
    shop_product_data = ShopProduct.objects.filter(
    is_delete=False
).annotate(
    total_sold_quantity=Sum('productorderdata__quantity')
).prefetch_related(
    Prefetch('shop_product', queryset=ShopProductImage.objects.filter(shop_product__is_delete=False).order_by("-id"), to_attr='images')
).select_related('subcategory', 'product_collection', 'country').order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/shop/view.html",
        {
            "shop_product_data": shop_product_data,
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_shop_product(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    shop_product = ShopProduct.objects.get(id=id)
    shop_product_images = ShopProductImage.objects.get(shop_product_id=id)
    product_imgs = ShopProductImageSubTable.objects.filter(
        shop_product_image_id=shop_product_images.id
    )
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/shop/view_product.html",
        {
            "shop_product": shop_product,
            "shop_product_images": shop_product_images,
            "product_imgs": product_imgs,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_shop_product(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        try:
            shop_product_id = request.POST.get("shop_product")
            shop_product = ShopProduct.objects.get(id=shop_product_id)
            shop_product.soft_delete()
            messages.success(request, "Record Deleted")
        except Exception as err:
            messages.error(request, "Deletion Failed")
    return redirect("view_shop_products")


@login_required(login_url="login")
def view_imagine_products(request):
    if is_normal_user(request):
        return redirect("web_login")
    imagine_product_data = ImagineProductImage.objects.filter(
        imagine_product__is_delete=False
    ).order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/imagine/view.html",
        {
            "imagine_product_data": imagine_product_data,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@csrf_exempt
def delete_imagine_product_image(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        product_image_id = request.POST.get("id")
        ImagineProductImageSubTable.objects.filter(id=product_image_id).delete()
    return JsonResponse({"status": True}, safe=False)


@login_required(login_url="login")
def add_imagine_product(request):
    if is_normal_user(request):
        return redirect("web_login")

    subcategories = SubCategory.objects.filter(is_active=True, category__name="Imagine")
    dress_types = DressType.objects.filter(is_active=True)
    colors = ProductColor.objects.filter(is_active=True)
    # shop products are related to imagine
    related_products = ShopProduct.objects.filter(is_active=True, is_delete=False)

    if request.method == "POST":
        post = request.POST

        name = post.get("name")
        alt_text = post.get("alt_text")
        og_title = post.get("og_title")
        og_description = post.get("og_description")
        description = post.get("description")
        subcategory_id = post.get("subcategory")
        dress_type_id = post.get("dress_type")
        product_color_id = post.get("color")
        related_product_list = post.getlist("related_products[]")

        primary_img = request.FILES.get("primary_image")
        pdf_img = request.FILES.get("pdf_image")
        og_img = request.FILES.get("og_image")
        images = request.FILES.getlist("product_images")

        try:
            imagine_product = ImagineProduct()
            imagine_product.name = name
            imagine_product.alt_text = alt_text
            imagine_product.og_title = og_title
            imagine_product.og_description = og_description
            imagine_product.description = description
            imagine_product.subcategory_id = subcategory_id
            imagine_product.dress_type_id = dress_type_id
            imagine_product.product_color_id = product_color_id
            imagine_product.related_product_list = related_product_list
            slug = imagine_product.subcategory.name + '-' + imagine_product.name
            imagine_product.slug = slugify(slug)
            url_slug = re.sub("[ ,./](?!.*--)", "-", name.lower())
            imagine_product.url_slug = url_slug
            imagine_product.save()

            imagine_product_imgs = ImagineProductImage()
            imagine_product_imgs.imagine_product_id = imagine_product.id

            if primary_img:
                imagine_product_imgs.primary_img = primary_img

            if pdf_img:
                imagine_product_imgs.pdf_img = pdf_img

            if og_img:
                imagine_product_imgs.og_img = og_img

            imagine_product_imgs.save()

            for i in range(0, len(images)):
                ImagineProductImageSubTable.objects.create(
                    imagine_product_image_id=imagine_product_imgs.id, images=images[i]
                )

            messages.success(request, "Imagine Product added successfully")

        except Exception as err:
            logging.error(traceback.format_exc())
            # messages.error(request,traceback.format_exc())
            messages.error(request, "Failed to add Imagine Product")

        return redirect("view_imagine_products")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/imagine/add.html",
        {
            "subcategories": subcategories,
            "dress_types": dress_types,
            "colors": colors,
            "related_products": related_products,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
        },
    )


@login_required(login_url="login")
def edit_imagine_product(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    subcategories = SubCategory.objects.filter(is_active=True, category__name="Imagine")
    dress_types = DressType.objects.filter(is_active=True)
    colors = ProductColor.objects.filter(is_active=True)

    imagine_product = ImagineProduct.objects.get(id=id, is_delete=False)
    imagine_product_image = ImagineProductImage.objects.get(imagine_product_id=id)
    product_imgs = ImagineProductImageSubTable.objects.filter(
        imagine_product_image_id=imagine_product_image.id
    )

    # shop product are related to imagine
    related_products = ShopProduct.objects.filter(is_active=True, is_delete=False)
    product_list = ast.literal_eval(imagine_product.related_product_list)
    product_list = list(map(int, product_list))

    if request.method == "POST":
        post = request.POST

        name = post.get("name")
        alt_text = post.get("alt_text")
        og_title = post.get("og_title")
        og_description = post.get("og_description")
        description = post.get("description")
        is_active = post.get("is_active")
        subcategory_id = post.get("subcategory")
        dress_type_id = post.get("dress_type")
        product_color_id = post.get("color")
        related_product_list = post.getlist("related_products[]")

        primary_img = request.FILES.get("primary_image")
        pdf_img = request.FILES.get("pdf_image")
        og_img = request.FILES.get("og_image")
        images = request.FILES.getlist("product_images")

        try:
            imagine_product.name = name
            imagine_product.alt_text = alt_text
            imagine_product.og_title = og_title
            imagine_product.og_description = og_description
            imagine_product.description = description
            imagine_product.is_active = is_active
            imagine_product.subcategory_id = subcategory_id
            imagine_product.dress_type_id = dress_type_id
            imagine_product.product_color_id = product_color_id
            imagine_product.related_product_list = related_product_list
            slug = imagine_product.subcategory.name + '-' + imagine_product.name
            imagine_product.slug = slugify(slug)

            url_slug = re.sub("[^A-Za-z0-9]+", "-", name.lower())
            imagine_product.url_slug = re.sub("[--]{2}", "", url_slug)
            imagine_product.save()

            if primary_img:
                imagine_product_image.primary_img = primary_img

            if pdf_img:
                imagine_product_image.pdf_img = pdf_img

            if og_img:
                imagine_product_image.og_img = og_img

            imagine_product_image.save()

            i = 1
            j = 5 - product_imgs.count()
            for img in images:
                if i > j:
                    break
                ImagineProductImageSubTable.objects.create(
                    images=img, imagine_product_image_id=imagine_product_image.id
                )
                i += 1

            messages.success(request, "product updated successfuly")
        except Exception as err:
            messages.error(request, "Failed to update product")

        return redirect("view_imagine_products")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/imagine/edit.html",
        {
            "subcategories": subcategories,
            "dress_types": dress_types,
            "colors": colors,
            "imagine_product": imagine_product,
            "imagine_product_image": imagine_product_image,
            "product_imgs": product_imgs,
            "related_products": related_products,
            "product_list": product_list,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_imagine_product(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    imagine_product = ImagineProduct.objects.get(id=id, is_delete=False)
    imagine_product_images = ImagineProductImage.objects.get(imagine_product_id=id)
    product_imgs = ImagineProductImageSubTable.objects.filter(
        imagine_product_image_id=imagine_product_images.id
    )
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/imagine/view_product.html",
        {
            "imagine_product": imagine_product,
            "imagine_product_images": imagine_product_images,
            "product_imgs": product_imgs,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_imagine_product(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        imagine_product_id = request.POST.get("imagine_product")
        try:
            imagine_product = ImagineProduct.objects.get(id=imagine_product_id)
            imagine_product.soft_delete()
            messages.success(request, "deleted record successfully")
        except:
            messages.error(request, "Something went wrong")
        return redirect("view_imagine_products")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/imagine/view.html",
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_subcategory(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = subcategory_template + "add.html"
    if request.method == "POST":
        post = request.POST
        name = post.get("name")
        heading = post.get("heading")
        description = post.get("description")
        meta_title = post.get("meta_title")
        meta_description = post.get("meta_description")
        meta_keyword = post.get("meta_keyword")
        og_title = post.get("og_title")
        og_description = post.get("og_description")
        permalink = post.get("permalink")
        priority = post.get("priority")
        is_active = post.get("is_active")
        category_id = 1  # post.get('category')
        banner_img = request.FILES.get("banner_image")
        og_img = request.FILES.get("og_image")

        try:
            if (
                not (name and not name.isspace())
                or not (heading and not heading.isspace())
                or not (description and not description.isspace())
                or not (meta_title and not meta_title.isspace())
                or not (meta_description and not meta_description.isspace())
                or not (meta_keyword and not meta_keyword.isspace())
                or not (og_title and not og_title.isspace())
                or not (og_description and not og_description.isspace())
                or not (priority and not priority.isspace())
            ):
                raise ValueError(empty_fields)

            if SubCategory.objects.filter(name=name).exists():
                messages.error(request, "Category Already Exist")
                return render(request, template_name, {"data": post})

            subcategory = SubCategory.objects.create(
                name=name,
                heading=heading,
                description=description,
                meta_title=meta_title,
                meta_description=meta_description,
                meta_keyword=meta_keyword,
                og_title=og_title,
                og_description=og_description,
                permalink=permalink,
                priority=priority,
                is_active=is_active,
                category_id=category_id,
                banner_img=banner_img,
                og_img=og_img,
            )

            messages.success(request, "SubCategory Added Successfully")
            return redirect("view_subcategories")

        except ValueError as val_err:
            messages.error(request, val_err)

        except Exception as err:
            messages.error(request, "Failed to Added category")
        model = Module.objects.all().order_by("id")
        return render(
            request,
            template_name,
            {
                "data": post,
                "m": permission(request),
                "module_list": helper(request),
                "model": model,
                "m_check": per(request),
            },
        )

    return render(
        request,
        template_name,
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def update_subcategory(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = subcategory_template + "edit.html"
    subcategory = SubCategory.objects.get(id=id)
 
    if int(id) in [1, 2, 3]:
        redirect_url = "view_subcategories"
    else:
        redirect_url = "view_imagine_subcategories"

    
    if request.method == "POST":
        try:
            post = request.POST
            name = post.get("name")
            heading = post.get("heading")
            description = post.get("description")
            meta_title = post.get("meta_title")
            meta_description = post.get("meta_description")
            meta_keyword = post.get("meta_keyword")
            og_title = post.get("og_title")
            og_description = post.get("og_description")
            permalink = post.get("permalink")
            priority = post.get("priority")
            is_active = post.get("is_active")
            category_id = 1  # post.get('category')
            banner_img = request.FILES.get("banner_image")
            og_img = request.FILES.get("og_image")

            if (
                not (name and not name.isspace())
                or not (heading and not heading.isspace())
                or not (description and not description.isspace())
                or not (meta_title and not meta_title.isspace())
                or not (meta_description and not meta_description.isspace())
                or not (meta_keyword and not meta_keyword.isspace())
                or not (og_title and not og_title.isspace())
                or not (og_description and not og_description.isspace())
                or not (priority and not priority.isspace())
            ):
                raise ValueError(empty_fields)

            if banner_img:
                subcategory.banner_img = banner_img

            if og_img:
                subcategory.og_img = og_img

            subcategory.name = name
            subcategory.heading = heading
            subcategory.description = description
            subcategory.meta_title = meta_title
            subcategory.meta_description = meta_description
            subcategory.meta_keyword = meta_keyword
            subcategory.og_title = og_title
            subcategory.og_description = og_description
            subcategory.permalink = permalink
            subcategory.priority = priority
            subcategory.is_active = is_active

            subcategory.save()
            messages.success(request, "SubCategory Updated Successfully")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("update_subcategory")

        except Exception as err:
            messages.error(request, "Failed To Update SubCategory")

        return redirect(redirect_url)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "data": subcategory,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
            "redirect_url": reverse(redirect_url)
        },
    )


@login_required(login_url="login")
def delete_subcategory(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("subcategory")
        subcategory = SubCategory.objects.get(id=id).delete()
        messages.success(request, "SubCategory Deleted Successfully")

    return redirect("view_subcategories")


@login_required(login_url="login")
def view_subcategories(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = subcategory_template + "view.html"
    subcategories = SubCategory.objects.filter(
        category__is_active=True, category__name="Shop"
    )
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "subcategories": subcategories,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )

@login_required(login_url="login")
def view_imagine_subcategories(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = subcategory_template + "view.html"
    subcategories = SubCategory.objects.filter(
        category__is_active=True, category__name="Imagine"
    )
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "subcategories": subcategories,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_subcategory_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = subcategory_template + "view_subcategory.html"
    subcategory = SubCategory.objects.get(id=id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "subcategory": subcategory,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
@csrf_exempt
def get_sub_categories(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        category_id = request.POST.get("category_id")
        sub_categories = SubCategory.objects.filter(
            category_id=category_id, category__is_active=True, is_active=True
        )

        options = ""
        for sub_category in sub_categories:
            options += (
                "<option value='"
                + str(sub_category.id)
                + "'>"
                + sub_category.name
                + "</option>"
            )

        return JsonResponse(options, safe=False)


@login_required(login_url="login")
def resend_mail(request):
    if is_normal_user(request):
        return redirect("web_login")

    try:
        email = request.POST.get("email").lower()
        password = random.randint(100000, 999999)

        try:
            user = User.objects.get(email=email, is_active=True)
            name = user.name
            mobile = user.mobile
            user.set_password(str(password))
            user.save()
        except:
            messages.error(request, "User Not Found")

        try:
            admin_changed_user_password_mail(email, name, password) 
        except:
            pass
        messages.success(request, "Password Sent On Email")

    except Exception as err:
        messages.error(request, "Fail To Send Mail")

    return redirect("view_users")

from random import randint
def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

@login_required(login_url="login")
def add_user(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        try:
            data = request.POST
            name = data.get("name")
            email = data.get("email").lower()
            mobile = data.get("mobile_number")
            country_code = data.get("country_code")
            if User.objects.filter(mobile=mobile, is_delete=False).exists():
                messages.error(request, "Number Already Exist")
                return redirect("add_user")
            if not (name and not name.isspace()) or not (email and not email.isspace()):
                raise ValueError(empty_fields)
            password = random.randint(100000, 999999)
            if User.objects.filter(email=email, is_delete=False).exists():
                messages.error(request, "User Already Exist")
                return redirect("add_user")
            user, created = User.objects.get_or_create(
                name=name,
                email=email,
                password=password,
                user_type="CUSTOMER",
                mobile=mobile,
                country_code=country_code,
            )
            user.set_password(str(user.password))
            user.is_verified = True
            digits = random_with_N_digits(8)
            code_name = name.replace(" ", "").upper()
            new_referral_code = f"{code_name}{digits}"
            user.referral_code = new_referral_code
            user.save()
            customer = create_customer(email)
            if not UserSubscriptions.objects.filter(user_id=user.id).exists():
                subscription_data = UserSubscriptions(user_id=user.id, customer_id=customer.id)
                subscription_data.save()
            Profile.objects.create(user_id=user.id)
            admin_added_user_mail(name, email, password)
            User.objects.filter(email=user.email).update(is_mail_send=True)
            messages.success(request, "User Created and Password Sent to Email and Mobile")
        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("add_user")
        except Exception as err:
            messages.error(request, "Failed to Create User")
        return redirect("view_users")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "user_management/add.html",
        {
            "user_types": USER_TYPE,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_user(request, user_id):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        try:
            data = request.POST
            name = data.get("name")
            is_active = data.get("is_active")
            if not (name and not name.isspace()):
                raise ValueError(empty_fields)

            user = User.objects.filter(id=user_id).update(
                name=name, is_active=is_active
            )
            messages.success(request, "User Updated")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("edit_user")

        except Exception as ex_err:
            messages.error(request, "Failed To Update")

        return redirect("view_users")

    user = User.objects.get(id=user_id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "user_management/edit.html",
        {   
            "user": user,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_user_detail(request, user_id):
    if is_normal_user(request):
        return redirect("web_login")
    user = User.objects.get(id=user_id)
    model = Module.objects.all().order_by("id")
    addresses = UserAddress.objects.filter(user_id=user_id)
    total_order = ProductOrder.objects.filter(user_id=user_id).count()
    total_completed_order = ProductOrder.objects.filter(user_id=user_id, order_status = "Completed").count()
    total_canceled_order = ProductOrder.objects.filter(user_id=user_id, order_status = "Canceled").count()
    return render(request, "user_management/view_user.html",
                                                            {
                                                             "total_completed_order":total_completed_order,
                                                             "total_canceled_order": total_canceled_order,   
                                                             "total_order":total_order,   
                                                             "user": user,
                                                             "addresses": addresses,
                                                             "m": permission(request),
                                                             "module_list": helper(request),
                                                             "model": model,
                                                             "m_check": per(request),
                                                            })


@login_required(login_url="login")
def delete_user(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        # try:
        user_id = request.POST.get("user_id")
        User.objects.get(id=user_id).delete()
        messages.success(request, "User Deleted")
        # except Exception as ex_err:
            # messages.error(request, "Failed To Delete User")

    return redirect("view_users")


@login_required(login_url="login")
def view_users(request):

    if is_normal_user(request):
        return redirect("web_login")

    # users = User.objects.filter(user_type__in=["CUSTOMER"]).order_by(
    #     "-id"
    # )
    users = UserAddress.objects.select_related("user").filter(user__user_type='CUSTOMER').order_by('-id')
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "user_management/view.html",
        {
            "users": users,
            "m": permission(request),
            "module_list": helper(request),
            "model": model,
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_sub_admin(request):
    if is_normal_user(request):
        return redirect("web_login")
    
    if request.method == "POST":
        try:
            model = Module.objects.all()

            data = request.POST
            username = data.get("name")
            email = data.get("email").lower()
            country_code = data.get("country_code")
            number = data.get("mobile_number")
            mobile = f"{country_code}{number}"
            country_code = data.get("country_code")
            
            if not (username and not username.isspace()) or not (email and not email.isspace()) or not (mobile and not mobile.isspace()):
                raise ValueError(empty_fields)
            
            if User.objects.filter(email=email, is_delete=False).exists():
                messages.error(request, "Sub Admin Already Exist")
                return redirect("add_sub_admin")

            password = random.randint(100000, 999999)

            user, created = User.objects.get_or_create(
                name=username,
                email=email,
                user_type="SUBADMIN",
                mobile=mobile,
                country_code=country_code,
            )

            user.set_password(str(password))
            user.save()
            
            for i in model:
                name = i.name.replace(" ", "")

                module = request.POST.get(f"checkbox[{name}]")
     
                add = request.POST.get(f"checkbox[{name}][add]")

                edit = request.POST.get(f"checkbox[{name}][edit]")

                show = request.POST.get(f"checkbox[{name}][show]")

                delete = request.POST.get(f"checkbox[{name}][delete]")
        
                if module != None:
                    data = ModulePermission.objects.create(
                        module_id=module,
                        add=add,
                        edit=edit,
                        view=show,
                        delete=delete,
                        user_id_id=user.id,
                    )
            try:
                add_sub_admin_mail(email, username, password)
            except:
                pass
            User.objects.filter(email=user.email).update(is_mail_send=True)
            messages.success(request, "Sub Admin Added Successfully")
        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("add_sub_admin")
        except Exception as err:
            messages.error(request, "Failed to Create User")
        return redirect("view_sub_admins")
    model = Module.objects.all().order_by("id").values()

    module_list = []
    parent_obj = Module.objects.filter(parent_id=0)
    parent_list = list()
    for i in parent_obj:
        obj_dict = dict()
        obj_dict["parent"] = i
        child_obj = Module.objects.filter(parent_id=i.id)

        obj_dict["child"] = child_obj
        module_list.append(obj_dict)

    m = permission(request)
    return render(
        request,
        "sub_admin_management/add.html",
        {
            "model": model,
            "m": m,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_sub_admin(request, sub_admin_id):
    subadmin_id = int(sub_admin_id)
    model = Module.objects.all()

    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        # try:
        data = request.POST
        name = data.get("name")
        email = data.get("email").lower()
        mobile = data.get("mobile")
        is_active = data.get("is_active")

        if not (name and not name.isspace()):
            raise ValueError(empty_fields)

        user = User.objects.filter(id=subadmin_id).update(
            name=name, email=email, mobile=mobile, is_active=is_active
        )
        data = ModulePermission.objects.filter(user_id=subadmin_id)
        data.delete()

        # c = 0
        for i in model:
            name = i.name.replace(" ", "")
            module = request.POST.get(f"checkbox[{name}]")
            add1 = request.POST.get(f"checkbox[{name}][add]")
            edit1 = request.POST.get(f"checkbox[{name}][edit]")
            show1 = request.POST.get(f"checkbox[{name}][show]")
            delete1 = request.POST.get(f"checkbox[{name}][delete]")
            if module != None:
                ModulePermission.objects.create(
                    module_id=module,
                    add=add1,
                    edit=edit1,
                    view=show1,
                    delete=delete1,
                    user_id_id=subadmin_id
                )
    sub_admin = User.objects.get(id=subadmin_id)

    # models = Module.objects.all().order_by("id").values()
    module_list = []
    parent_obj = Module.objects.filter(parent_id=0)
    # parent_list = list()
    for i in parent_obj:
        obj_dict = dict()
        obj_dict["parent"] = i
        child_obj = Module.objects.filter(parent_id=i.id)
        obj_dict["child"] = child_obj

        if i.url:
            obj_dict["url"] = reverse(i.url)

        for child in child_obj:
            child.child_url = reverse(child.url)
            child.save()

        module_list.append(obj_dict)

    m_check = ModulePermission.objects.filter(user_id=sub_admin.id)
    return render(
        request,
        "sub_admin_management/edit1.html",
        {
            "sub_admin": sub_admin,
            "m": permission(request),
            "permission": m_check,
            "m_check": per(request),
            "module_list": helper(request),
        },
    )


@login_required(login_url="login")
def view_sub_admin_detail(request, sub_admin_id):
    if is_normal_user(request):
        return redirect("web_login")

    sub_admin = User.objects.get(id=sub_admin_id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "sub_admin_management/view_sub_admin.html",
        {
            "sub_admin": sub_admin,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_sub_admin(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        try:
            id = request.POST.get("sub_admin")
            User.objects.get(id=id).delete()
            messages.success(request, "Successfully Deleted Sub Admin")

        except Exception as ex_err:
            messages.error(request, "Failed To Delete Sub Admin")

    return redirect("view_sub_admins")


@login_required(login_url="login")
def view_sub_admins(request):
    if is_normal_user(request):
        return redirect("web_login")

    sub_admins = User.objects.filter(user_type="SUBADMIN").order_by(
        "-id"
    )
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "sub_admin_management/view.html",
        {
            "sub_admins": sub_admins,
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


super_admin_template = "super_admin_management/"


@login_required(login_url="login")
def add_super_admin(request):
    if is_normal_user(request):
        return redirect("web_login")

    template = super_admin_template + "add.html"
    if request.method == "POST":
        # try:
        data = request.POST
        name = data.get("name")
        email = data.get("email").lower()
        country_code = data.get('country_code')
        number = data.get("mobile_number")
        mobile = f"{country_code}{number}"
        country_code = data.get("country_code")

        if (
            not (name and not name.isspace())
            or not (email and not email.isspace())
            or not (mobile and not mobile.isspace())
        ):
            raise ValueError(empty_fields)

        password = random.randint(100000, 999999)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Exist")
            return render(request, template, {"post_data": request.POST})

        user, created = User.objects.get_or_create(
            name=name,
            email=email,
            password=password,
            user_type="SUPERADMIN",
            mobile=mobile,
            country_code=country_code,
            is_superuser=True,
            is_staff=True,
            is_verified = True
        )
        user.set_password(str(user.password))
        user.save()

        ###### mail send start ###########
        superadmin_create_mail(email, password, name)
        ###### mail send end ###########

        User.objects.filter(email=user.email).update(is_mail_send=True)
        messages.success(request, "Super Admin Added Successfully")

        # except ValueError as val_err:
        #     messages.error(request, val_err)
        #     return render(request, template, {"post_data": request.POST})

        # except Exception as err:
        #     messages.error(request, "Failed to Create Super Admin")

        return redirect("view_super_admins")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template,
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_super_admin(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template = super_admin_template + "edit.html"
    super_admin = User.objects.get(id=id)

    if request.method == "POST":
        try:
            data = request.POST
            name = data.get("name")
            email = data.get("email").lower()
            country_code = data.get('country_code')
            number = data.get("mobile")
            mobile = f"{country_code}{number}"
            is_active = data.get("is_active")

            if (
                not (name and not name.isspace())
                or not (email and not email.isspace())
                or not (mobile and not mobile.isspace())
            ):
                raise ValueError(empty_fields)

            super_admin.name = name
            super_admin.email = email
            super_admin.mobile = mobile
            super_admin.is_active = is_active
            super_admin.save()

            messages.success(request, "Details Updated")

        except ValueError as val_err:
            messages.error(request, val_err)
            return render(request, template, {"post_data": super_admin})

        except Exception as ex_err:
            messages.error(request, "Failed To Update Super Admin Details")

        return redirect("view_super_admins")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template,
        {
            "user": super_admin,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_super_admin_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template = super_admin_template + "view_user.html"
    super_admin = User.objects.get(id=id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template,
        {
            "user": super_admin,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_super_admin(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        # try:
        id = request.POST.get("user")
        User.objects.get(id=id).delete()
        messages.success(request, "Successfully Deleted Super Admin")
        # except Exception as ex_err:
            # messages.error(request, "Failed To Delete Super Admin")

    return redirect("view_super_admins")


@login_required(login_url="login")
def view_super_admins(request):
    if is_normal_user(request):
        return redirect("web_login")

    template = super_admin_template + "view.html"
    super_admin = User.objects.filter(user_type="SUPERADMIN").order_by(
        "-id"
    )
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template,
        {
            "users": super_admin,
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_social_media(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        try:
            name = request.POST.get("name").strip()
            link = request.POST.get("link")
            SocialMedia.objects.create(name=name, link = link)

            if not (name and not name.isspace()):
                raise ValueError(empty_fields)

            messages.success(request, "Social Media Added")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("add_social_media")

        except Exception as err:
            messages.error(request, "Failed to Add Social Media")

        return redirect("view_social_media")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "social_media_management/add.html",
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_social_media(request):
    if is_normal_user(request):
        return redirect("web_login")

    social_media = SocialMedia.objects.filter(is_active=True)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "social_media_management/view.html",
        {
            "social_media": social_media,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_social_media(request, social_media_id):
    if is_normal_user(request):
        return redirect("web_login")

    sm = SocialMedia.objects.get(id=social_media_id, is_active=True)

    if request.method == "POST":
        try:
            if not sm:
                raise EmptyResultSet("Object Not Found")
            link = request.POST.get("link")
            sm.link = link
            sm.save()
            messages.success(request, "Social Media Updated")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("edit_social_media")

        except Exception as err:
            messages.error(request, "Failed to Update Social Media")

        return redirect("view_social_media")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "social_media_management/edit.html",
        {
            "social_media": sm,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_social_media(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("sm_id")
        SocialMedia.objects.get(id=id).delete()
        messages.success(request, "Deleted")
        return redirect("view_social_media")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "social_media_management/view.html",
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_dress_type(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = dress_type_template + "add.html"
    if request.method == "POST":
        try:
            post = request.POST
            name = post.get("name")
            description = post.get("description")
            meta_title = post.get("meta_title")
            meta_description = post.get("meta_description")
            meta_keyword = post.get("meta_keyword")
            og_title = post.get("og_title")
            og_description = post.get("og_description")
            permalink = post.get("permalink")
            priority = post.get("priority")
            is_active = post.get("is_active")
            category_id = 2  # post.get('category')
            og_img = request.FILES.get("og_image")

            if (
                not (name and not name.isspace())
                or not (description and not description.isspace())
                or not (meta_title and not meta_title.isspace())
                or not (meta_description and not meta_description.isspace())
                or not (meta_keyword and not meta_keyword.isspace())
                or not (og_title and not og_title.isspace())
                or not (og_description and not og_description.isspace())
                or not (priority and not priority.isspace())
            ):
                raise ValueError(empty_fields)

            if DressType.objects.filter(name=name).exists():
                messages.error(request, "DressType Already Exist")
                return redirect("add_dress_type")

            url_slug = re.sub("[^A-Za-z0-9]+", "-", name.lower())

            DressType.objects.create(
                name=name,
                description=description,
                meta_title=meta_title,
                meta_description=meta_description,
                meta_keyword=meta_keyword,
                og_title=og_title,
                og_description=og_description,
                permalink=permalink,
                priority=priority,
                is_active=is_active,
                category_id=category_id,
                og_img=og_img,
                url_slug=re.sub("[--]{2}", "", url_slug),
            )

            messages.success(request, "dress type added successfully")
            return redirect("view_dress_types")

        except ValueError as val_err:
            messages.error(request, val_err)
            redirect("add_dress_type")

        except Exception as err:
            messages.error(request, "failed to add dress type")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "data": request.POST,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_dress_types(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = dress_type_template + "view.html"
    dress_types = DressType.objects.all().order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "dress_types": dress_types,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_dress_type(request, dress_type_id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = dress_type_template + "edit.html"
    dress_type = DressType.objects.get(id=dress_type_id)

    if request.method == "POST":
        try:
            post = request.POST
            name = post.get("name")
            description = post.get("description")
            meta_title = post.get("meta_title")
            meta_description = post.get("meta_description")
            meta_keyword = post.get("meta_keyword")
            og_title = post.get("og_title")
            og_description = post.get("og_description")
            permalink = post.get("permalink")
            priority = post.get("priority")
            is_active = post.get("is_active")
            category_id = 2  # post.get('category')
            og_img = request.FILES.get("og_image")

            if (
                not (name and not name.isspace())
                or not (description and not description.isspace())
                or not (meta_title and not meta_title.isspace())
                or not (meta_description and not meta_description.isspace())
                or not (meta_keyword and not meta_keyword.isspace())
                or not (og_title and not og_title.isspace())
                or not (og_description and not og_description.isspace())
                or not (priority and not priority.isspace())
            ):
                raise ValueError(empty_fields)

            if og_img:
                dress_type.og_img = og_img

            dress_type.name = name
            dress_type.description = description
            dress_type.meta_title = meta_title
            dress_type.meta_description = meta_description
            dress_type.meta_keyword = meta_keyword
            dress_type.og_title = og_title
            dress_type.og_description = og_description
            dress_type.permalink = permalink
            dress_type.priority = priority
            dress_type.is_active = is_active

            dress_type.save()
            messages.success(request, "dress type Updated successfully")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("edit_dress_type")

        except Exception as err:
            messages.error(request, "failed to update dress type")

        return redirect("view_dress_types")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "data": dress_type,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_dress_type(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("dress_type")
        DressType.objects.get(id=id).delete()
        messages.success(request, "Deleted Successfully")

    return redirect("view_dress_types")


@login_required(login_url="login")
def view_dress_type_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = dress_type_template + "view_dress_type.html"
    dress_type = DressType.objects.get(id=id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "dress_type": dress_type,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_collection(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = collection_template + "add.html"
    if request.method == "POST":
        post = request.POST
        name = post.get("name")
        priority = post.get("priority")
        permalink = post.get("permalink")
        category_name = post.get("category")
        is_active = post.get("is_active")

        try:
            if not (name and not name.isspace()):
                raise ValueError(empty_fields)
            elif ProductCollection.objects.filter(name=name).exists():
                messages.error(request, "Collection Already Exist")
                return redirect("add_collection")

            if not category_name:
                category_name = "Shop"

            category = Category.objects.get(name=category_name)
            ProductCollection.objects.create(
                name=name,
                priority=priority,
                permalink=permalink,
                category_id=category.id,
                is_active=is_active,
            )
            messages.success(request, "collection added successfully")
            return redirect("view_collections")
        except ValueError as val_err:
            messages.error(request, val_err)
            redirect("add_collection")
        except Exception as err:
            messages.error(request, "failed to add collection")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_collections(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = collection_template + "view.html"
    product_collections = ProductCollection.objects.all().order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "product_collections": product_collections,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_collection_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = collection_template + "view_collection.html"
    collection = ProductCollection.objects.get(id=id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "collection": collection,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_collection(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = collection_template + "edit.html"
    product_collection = ProductCollection.objects.get(id=id)

    if request.method == "POST":
        try:
            name = request.POST.get("name").strip()

            if not (name and not name.isspace()):
                raise ValueError(empty_fields)

            product_collection.name = name
            product_collection.is_active = request.POST.get("is_active")
            url_slug = re.sub("[^A-Za-z0-9]+", "-", name.lower())
            product_collection.url_slug = re.sub("[--]{2}", "", url_slug)
            product_collection.save()

            messages.success(request, "Collection Updated successfully")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("edit_collection")

        except Exception as err:
            messages.error(request, "failed to update collection")

        return redirect("view_collections")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "collection": product_collection,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_collection(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = collection_template + "view.html"

    if request.method == "POST":

        try:
            id = request.POST.get("collection")
            ProductCollection.objects.get(id=id).delete()
            messages.success(request, "Deleted Collection Successfully")

        except Exception as err:
            messages.error(request, "Failed to delete collection")

        return redirect("view_collections")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
         },
    )


@login_required(login_url="login")
def add_color(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = color_template + "add.html"

    if request.method == "POST":
        try:
            post = request.POST
            name = post.get("name")
            description = post.get("description")
            detail_description = post.get("editor")
            meta_title = post.get("meta_title")
            meta_description = post.get("meta_description")
            meta_keyword = post.get("meta_keyword")
            og_title = post.get("og_title")
            og_description = post.get("og_description")
            text_color = post.get("text_color")
            image_color_code = post.get("image_color_code")
            permalink = post.get("permalink")
            priority = post.get("priority")
            is_active = post.get("is_active")
            category_id = 2  # post.get('category')
            thumbnail_img = request.FILES.get("thumbnail_image")
            banner_img = request.FILES.get("banner_image")
            og_img = request.FILES.get("og_image")

            if (
                not (name and not name.isspace())
                or not (description and not description.isspace())
                or not (detail_description and not detail_description.isspace())
                or not (meta_title and not meta_title.isspace())
                or not (meta_description and not meta_description.isspace())
                or not (meta_keyword and not meta_keyword.isspace())
                or not (og_title and not og_title.isspace())
                or not (og_description and not og_description.isspace())
                or not (text_color and not text_color.isspace())
                or not (image_color_code and not image_color_code.isspace())
                or not (priority and not priority.isspace())
            ):
                raise ValueError(empty_fields)

            if ProductColor.objects.filter(name=name).exists():
                messages.error(request, "Color Already Exist")
                return redirect("add_color")

            url_slug = re.sub("[^A-Za-z0-9]+", "-", name.lower())

            ProductColor.objects.create(
                name=name,
                description=description,
                detail_description=detail_description,
                meta_title=meta_title,
                meta_description=meta_description,
                meta_keyword=meta_keyword,
                og_title=og_title,
                og_description=og_description,
                text_color=text_color,
                image_color_code=image_color_code,
                permalink=permalink,
                priority=priority,
                is_active=is_active,
                category_id=category_id,
                thumbnail_img=thumbnail_img,
                banner_img=banner_img,
                og_img=og_img,
                url_slug=re.sub("[--]{2}", "", url_slug),
            )

            messages.success(request, "color added successfully")
            return redirect("view_colors")

        except ValueError as val_err:
            messages.error(request, val_err)
            redirect("add_color")

        except Exception as err:
            messages.error(request, "failed to add color")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "data": request.POST,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_colors(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = color_template + "view.html"
    colors = ProductColor.objects.all().order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "colors": colors,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_color_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = color_template + "view_color.html"
    color = ProductColor.objects.get(id=id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "color": color,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_color(request, color_id):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = color_template + "edit.html"
    color = ProductColor.objects.get(id=color_id)

    if request.method == "POST":
        try:
            post = request.POST
            name = post.get("name")
            description = post.get("description")
            detail_description = post.get("editor")
            meta_title = post.get("meta_title")
            meta_description = post.get("meta_description")
            meta_keyword = post.get("meta_keyword")
            og_title = post.get("og_title")
            og_description = post.get("og_description")
            text_color = post.get("text_color")
            image_color_code = post.get("image_color_code")
            permalink = post.get("permalink")
            priority = post.get("priority")
            is_active = post.get("is_active")
            category_id = 2  # post.get('category')
            thumbnail_img = request.FILES.get("thumbnail_image")
            banner_img = request.FILES.get("banner_image")
            og_img = request.FILES.get("og_image")

            if (
                not (name and not name.isspace())
                or not (description and not description.isspace())
                or not (detail_description and not detail_description.isspace())
                or not (meta_title and not meta_title.isspace())
                or not (meta_description and not meta_description.isspace())
                or not (meta_keyword and not meta_keyword.isspace())
                or not (og_title and not og_title.isspace())
                or not (og_description and not og_description.isspace())
                or not (text_color and not text_color.isspace())
                or not (image_color_code and not image_color_code.isspace())
                or not (priority and not priority.isspace())
            ):
                raise ValueError(empty_fields)

            color.name = name
            color.description = description
            color.detail_description = detail_description
            color.meta_title = meta_title
            color.meta_description = meta_description
            color.meta_keyword = meta_keyword
            color.og_title = og_title
            color.og_description = og_description
            color.text_color = text_color
            color.image_color_code = image_color_code
            color.permalink = permalink
            color.priority = priority
            color.is_active = is_active

            url_slug = re.sub("[^A-Za-z0-9]+", "-", name.lower())
            color.url_slug = re.sub("[--]{2}", "", url_slug)

            if thumbnail_img:
                color.thumbnail_img = thumbnail_img

            if banner_img:
                color.banner_img = banner_img

            if og_img:
                color.og_img = og_img

            color.save()

            messages.success(request, "Color Updated")

        except ValueError as val_err:
            messages.error(request, val_err)
            return redirect("edit_color", color_id)

        except Exception as err:
            messages.error(request, "failed to update color")

        return redirect("view_colors")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "data": color,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_color(request):
    if is_normal_user(request):
        return redirect("web_login")

    template_name = color_template + "view.html"

    if request.method == "POST":
        id = request.POST.get("color")
        ProductColor.objects.get(id=id).delete()

        return redirect("view_colors")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template_name,
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


# @login_required(login_url='login')
# def dynamic_sidebar(request):
#     modules = Modules.objects.filter(is_active=True, is_delete=False)


@login_required(login_url="login")
def add_blog(request):
    # try:
    if is_normal_user(request):
        return redirect("web_login")

    Shop = ShopProduct.objects.all()
    Imagine = ImagineProduct.objects.all()
    categories = BlogCategory.objects.all()

    if request.method == "POST":
        try:
            r_post = request.POST
            heading = r_post.get("heading")
            other_important_info = r_post.get("other_important_info")
            category = r_post.get("category")
            subcategory = r_post.get("sub_category")
            content = r_post.get("editor")
            is_comment = r_post.get("comment")
            is_publish = r_post.get("is_publish")
            is_blog_schedule = eval(r_post.get("is_blog_schedule")) if r_post.get("is_blog_schedule") else False
            schedule_time = r_post.get("schedule_time")
            image = request.FILES.get("image")
            video = request.FILES.get("video")
            shop_id_str = r_post.getlist("related_shop[]")
            shop_id_int = []
            for y in shop_id_str:
                x = int(y)
                shop_id_int.append(x)

            imagine_id_str = r_post.getlist("related_imagine[]")
            imagine_id_int = []
            for y in imagine_id_str:
                x = int(y)
                imagine_id_int.append(x)

            if not (content and not content.isspace()):
                raise ValueError("Please Give content")

            if is_blog_schedule:
                date_time_format = "%Y-%m-%d %H:%M"  # The format
                publish_at = datetime.strptime(str(schedule_time), date_time_format).replace(tzinfo=None)
            else:
                publish_at = timezone.now()

            blog_data = Blog.objects.create(
                heading=heading,
                image=image,
                video=video,
                other_important_info=other_important_info,
                blog_category_id=category,
                shop=shop_id_int,
                imagine=imagine_id_int,
                content=content,
                is_comment=is_comment,
                is_publish=is_publish,
                is_blog_schedule=is_blog_schedule,
                publish_at=publish_at,
                sub_category_id = subcategory
            )
            blog_data.create_slug()
            blog_data.save()
            messages.success(request, "blog added successfully")

            recipient_list = []
            userdata = BlogSubscriber.objects.all()
            if not userdata:
                messages.error(request, "No Subscriber")
            for i in userdata:
                recipient_list.append(i.email)
            new_blog_post(recipient_list, heading)
            return redirect("view_blogs")
            
        except ValueError as val_err:
            messages.error(request, val_err)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "blog_management/add.html",
        {
            "Shop": Shop,
            "Imagine": Imagine,
            "categories": categories,
            "data": request.POST,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )
    # except:
    #     messages.error(request, "Something Went Wrong")
    #     return redirect("view_blogs")


@login_required(login_url="login")
def edit_blog(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    blog = Blog.objects.get(id=id)
    categories = BlogCategory.objects.all()
    subcategories = BlogSubCategory.objects.all()

    if request.method == "POST":
        try:
            r_post = request.POST
            heading = r_post.get("heading")
            other_important_info = r_post.get("other_important_info")
            category = r_post.get("category")
            subcategory = r_post.get("sub_category")
            content = r_post.get("editor")
            is_comment = r_post.get("comment")
            is_publish = r_post.get("publish")
            is_blog_schedule = eval(r_post.get("is_blog_schedule")) if r_post.get("is_blog_schedule") else False
            schedule_time = r_post.get("schedule_time")
            image = request.FILES.get("image")
            video = request.FILES.get("video")

            if not (content and not content.isspace()):
                raise ValueError("Please Enter Content")

            if is_blog_schedule:
                date_time_format = "%Y-%m-%d %H:%M"
                publish_at = datetime.strptime(str(schedule_time), date_time_format).replace(tzinfo=None)
            else:
                publish_at = timezone.now()

            if image:
                blog.image = image

            if video:
                blog.video = video

            blog.heading = heading
            blog.other_important_info = other_important_info
            blog.blog_category_id = category
            blog.content = content
            blog.is_comment = is_comment
            blog.is_publish = is_publish
            blog.publish_at = publish_at
            blog.sub_category_id = subcategory
            blog.is_blog_schedule = is_blog_schedule
            blog.create_slug()
            blog.save()

            messages.success(request, "blog updated successfully")
            return redirect("view_blogs")

        except ValueError as val_err:
            messages.error(request, val_err)

    model = Module.objects.all().order_by("id")
    return render(
        request,
        "blog_management/edit.html",
        {
            "blog": blog,
            "categories": categories,
            "subcategories": subcategories,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_blog(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("blog")
        Blog.objects.get(id=id).delete()
        messages.success(request, "Blog Deleted")
        return redirect("view_blogs")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "blog_management/view.html",
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_blogs(request):
    if is_normal_user(request):
        return redirect("web_login")

    blogs = Blog.objects.all().order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "blog_management/view.html",
        {
            "blogs": blogs,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


    


@login_required(login_url="login")
def view_blog_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    blog = Blog.objects.get(id=id)
    blog_comments = BlogComment.objects.filter(blog_id=id)
    blog_comments_count = blog_comments.count()
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "blog_management/view_blog.html",
        {   "blog_comments_count": blog_comments_count,
            "blog": blog,
            "blog_comments": blog_comments,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


blog_category_template = "blog_management/blog_categories/"

# Blog Category Start
@login_required(login_url="login")
def add_blog_category(request):
    if is_normal_user(request):
        return redirect("web_login")

    template = blog_category_template + "add.html"

    if request.method == "POST":
        name = request.POST.get("name").strip()
        description = request.POST.get("description")

        try:
            if BlogCategory.objects.filter(name=name).exists():
                messages.error(request, "Blog Category Already Exist")
                return render(request, template, {"data": request.POST})

            BlogCategory.objects.create(name=name, description=description)
            messages.success(request, "Blog Category Added Successfully")
            return redirect("view_blog_categories")
        except Exception as err:
            messages.error(request, "Failed to add Blog category")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template,
        {
            "data": request.POST,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_blog_categories(request):
    if is_normal_user(request):
        return redirect("web_login")

    template = blog_category_template + "view.html"

    blog_categories = BlogCategory.objects.all().order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template,
        {
            "blog_categories": blog_categories,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_blog_category(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    try:
        template = blog_category_template + "edit.html"
        blog_category = BlogCategory.objects.get(id=id)

        if request.method == "POST":
            name = request.POST.get("name").strip()
            description = request.POST.get("description")
            blog_category.name = name
            blog_category.description = description
            blog_category.save()

            messages.success(request, "Blog Category Updated Successfully")
            return redirect("view_blog_categories")

    except Exception as err:
        messages.error(request, "Failed to Update Blog Category")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        template,
        {
            "blog_category": blog_category,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_blog_category(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("blog_category")
        if not Blog.objects.filter(blog_category_id = id).exists():
            BlogCategory.objects.get(id=id).delete()
            messages.success(request, "Blog Category Deleted Successfully")
        else:
            messages.error(request, "Category is used in Blog, Can't be Deleted")

    return redirect("view_blog_categories")
# Blog Category End
# Blog Subcategory Start
@login_required(login_url="login")
def add_blog_subcategory(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        try:
            blog_category_data = BlogCategory.objects.all()
        except:
            blog_category_data = None

        if request.method == "POST":
            blog_category_id = request.POST.get("category") 
            name = request.POST.get("name")
            Subcategory = BlogSubCategory.objects.create(name = name, category_id = blog_category_id)
            Subcategory_id = Subcategory.id
            messages.success(request, "Sub Category Created")
            return redirect("blog_subcategory")
        model = Module.objects.all().order_by("id")    
        return render(request, "blog_management/blog_subcategories/add.html", {"blog_category_data": blog_category_data, "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request)})    
    except:
        messages.error(request, "Somenthing Went Wrong")
        return redirect("blog_subcategory")


@login_required(login_url="login")
def blog_subcategory(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        try:
            blog_category_data = BlogCategory.objects.all()
        except:
            blog_category_data = None
        subcategory_data = BlogSubCategory.objects.all()
        model = Module.objects.all().order_by("id")
        return render(request, "blog_management/blog_subcategories/view.html", {"subcategory_data": subcategory_data, "blog_category_data": blog_category_data, "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request)})    
    except:
        messages.error(request, "Somenthing Went Wrong")
        return redirect("")
@csrf_exempt
def subcategory_data(request):
    category_id = request.POST.get("category_id")
    subcategory_data = BlogSubCategory.objects.filter(category_id = category_id)
    blog_data = BlogSubCategorySerializer(subcategory_data, many=True)
    return JsonResponse(blog_data.data, safe=False)



@login_required(login_url="login")
def edit_subcategory(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subcategory_data = BlogSubCategory.objects.get(id = id)
        blog_category_data = BlogCategory.objects.all()
        if request.method == "POST":
            name = request.POST.get("name")
            blog_category_id = request.POST.get("category")
            subcategory_data.name = name
            subcategory_data.category_id = blog_category_id
            subcategory_data.save()
            messages.success(request, "Subcategory Edited")
            return redirect("blog_subcategory")
        model = Module.objects.all().order_by("id")
        return render(request, "blog_management/blog_subcategories/edit.html", 
                        {"subcategory_data": subcategory_data, 
                            "blog_category_data": blog_category_data, 
                            "m": permission(request),
                            "model": model,
                            "module_list": helper(request),
                            "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("blog_subcategory")
       

def delete_subcategory(request):
    try:
        sub_category_id = request.POST.get("subcategory")
        if not Blog.objects.filter(sub_category_id = sub_category_id).exists():
            BlogSubCategory.objects.get(id = sub_category_id).delete()
            messages.success(request, "Sub Category Deleted")
        else:
            messages.error(request, "Subcategory is used in Blog, Cant't be Deleted")  
        return redirect("blog_subcategory")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("blog_subcategory")
# Blog Subcategory End

@login_required(login_url="login")
def add_country(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        try:
            name = request.POST.get("name").strip()
            heading = request.POST.get("heading")
            initial_paragraph = request.POST.get("initial_paragraph")
            body_paragraph = request.POST.get("body_paragraph")
            # latitude = request.POST.get("latitude")
            # longitude = request.POST.get("longitude")
            is_active = request.POST.get("is_active")
            flag_img = request.FILES.get("flag_img")
            map_img = request.FILES.get("map_img")

            if (
                not (name and not name.isspace())
                or not (heading and not heading.isspace())
            ):
                raise ValueError(empty_fields)

            if Country.objects.filter(name=name).exists():
                messages.error(request, "Country Already Exist")
                return render(
                    request,
                    "product_management/country/add.html",
                    {"data": request.POST},
                )

            if Country.objects.filter(name=name).exists():
                messages.error(request, "Country Already Exist")
                return render(
                    request,
                    "product_management/country/add.html",
                    {
                        "data": request.POST,
                        "m": permission(request),
                        "module_list": helper(request),
                        "m_check": per(request),
                    },
                )

            Country.objects.create(
                name=name,
                heading=heading,
                is_active=is_active,
                initial_paragraph=initial_paragraph,
                body_paragraph=body_paragraph,
                flag_img=flag_img,
                map_img=map_img,
            )
            messages.success(request, "Country Added Successfully")
            return redirect("view_countries")

        except ValueError as val_err:
            messages.error(request, val_err)

        except Exception as err:
            messages.error(request, "Failed to Add Country")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/country/add.html",
        {
            "data": request.POST,
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_countries(request):
    if is_normal_user(request):
        return redirect("web_login")

    countries = Country.objects.all().order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/country/view.html",
        {
            "countries": countries,
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_country(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    try:
        country = Country.objects.get(id=id)
    except:
        messages.error(request, "Country Not Found")
        return redirect("view_countries")

    try:
        if request.method == "POST":
            name = request.POST.get("name").strip()
            heading = request.POST.get("heading")
            initial_paragraph = request.POST.get("initial_paragraph")
            body_paragraph = request.POST.get("body_paragraph")
            latitude = request.POST.get("latitude")
            longitude = request.POST.get("longitude")
            is_active = request.POST.get("is_active")
            flag_img = request.FILES.get("flag_img")
            map_img = request.FILES.get("map_img")

            if (
                not (name and not name.isspace())
                or not (heading and not heading.isspace())
            ):
                raise ValueError(empty_fields)

            country.name = name
            country.heading = heading
            country.initial_paragraph = initial_paragraph
            country.body_paragraph = body_paragraph
            country.latitude = latitude
            country.longitude = longitude
            country.is_active = is_active

            if flag_img:
                country.flag_img = flag_img

            if map_img:
                country.map_img = map_img

            country.save()
            messages.success(request, "Country Update Successfully")
            return redirect("view_countries")

    except ValueError as val_err:
        messages.error(request, val_err)

    except Exception as err:
        messages.error(request, "Failed to Update Country")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/country/edit.html",
        {
            "data": country,
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_country(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("country_id")
        if not ShopProduct.objects.filter(country_id = id).exists() and not SheroDolls.objects.filter(country_id = id).exists():
            Country.objects.get(id=id).delete()
            messages.success(request, "Deleted")
        else:
            messages.error(request, "Country is used in Products, Can't be Deleted")
        return redirect("view_countries")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/country/view.html",
        {
            "model": model,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_country_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    country = Country.objects.get(id=id)
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "product_management/country/view_country.html",
        {
            "country": country,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_order_charges(request):
    if is_normal_user(request):
        return redirect("web_login")

    order_charges = OrderCharge.objects.all()
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "order_charges/view.html",
        {
            "order_charges": order_charges,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_order_charge(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    charge = OrderCharge.objects.get(id=id)
    if request.method == "POST":
        name = request.POST.get("name").strip()
        percent = request.POST.get("percent")
        charge.name = name
        charge.percentage = percent
        charge.save()
        return redirect("view_order_charges")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "order_charges/edit.html",
        {
            "charge": charge,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request)
        },
    )

def subscribers(request):
    subscribers = BlogSubscriber.objects.all().order_by('-id')
    model = Module.objects.all().order_by("id")
    return render (request, "blog_management/blog_subscribers/subscribers.html", {"subscribers": subscribers,  "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request)})


# Blog User Start
def blog_user(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        blog_user = BlogUser.objects.order_by("user_id").distinct("user_id")
        model = Module.objects.all().order_by("id")
        return render(
            request,
            "blog_management/blog_user/blog_user.html",
            {
                "bloguser": blog_user,
                "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request),
            },
        )
    except Exception as err:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")


def delete_blog_user(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("delete_blog_user")
        BlogUser.objects.filter(user_id=id).delete()
        return redirect("blog_user")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("blog_user")


def view_blog_user(request, user):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        blog = BlogUser.objects.filter(user_id=user).distinct("blog_id")
        model = Module.objects.all().order_by("id")
        return render(
            request,
            "blog_management/blog_user/view_blog_user.html",
            {
                "blogcomment": blog,
                "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request),
            },
        )
    except:
        messages.error(request, "Something Went Wrong")
        return blog_user(request)


def edit_blog_user(request, id):
    user_data = User.objects.get(id = id)
    if request.method == "POST":
        can_comment = request.POST.get("can_comment")
        user_data.can_comment = can_comment
        user_data.save()
        messages.success(request, "Edited")
        return redirect("blog_user")
    model = Module.objects.all().order_by("id")
    return render(
            request,
            "blog_management/blog_user/edit_blog_user.html",
            {
                "blog_user_data": user_data,
                "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request),
            },
        )    


def view_blog_user_comment(request, blog, user):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        blog_data = Blog.objects.get(id=blog)
        user_data = User.objects.get(id=user)
        user_name = user_data.name
        comments_data = BlogComment.objects.filter(user_id=user)
        comments = comments_data.filter(blog_id=blog)
        total = comments.count()
        model = Module.objects.all().order_by("id")
        return render(
            request,
            "blog_management/blog_user/blog_user_comment.html",
            {
                "total": total,
                "comments": comments,
                "name": user_name,
                "blog_data": blog_data,
                "m": permission(request),
                "model": model,
                "user": user,
                "module_list": helper(request),
                "m_check": per(request),
            },
        )
    except:
        messages.error(request, "Something Went Wrong")
        return view_blog_user(request, user)


def delete_blog_user_comment(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        id = request.POST.get("blog_user_comment")
        data = id.split(",")
        blog_id = data[0]
        user_id = data[1]
        try:
            BlogComment.objects.filter(blog_id=blog_id).delete()
            messages.success(request, "Deleted")
            return view_blog_user(request, user_id)
        except:
            messages.error(request, "Something Went Wrong")
            return view_blog_user(request, user_id)


def delete_comment(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        try:
            id = request.POST.get("blog_comment")
            data = id.split(",")
            comment_id = data[0]
            blog_id = data[1]
            user_id = data[2]
            blog = BlogComment.objects.filter(blog_id=blog_id)
            user = blog.filter(user_id=user_id).count()
            total = (
                BlogComment.objects.filter(user_id=user_id).distinct("blog_id").count()
            )
            if total == 1:
                try:
                    if user == 1:
                        comment = BlogComment.objects.get(id=comment_id)
                        comment.delete()
                        messages.success(request, "Deleted")
                        return redirect("blog_user")
                    else:
                        comment = BlogComment.objects.get(id=comment_id)
                        comment.delete()
                        messages.success(request, "Deleted")
                        return view_blog_user_comment(request, blog_id, user_id)
                except:
                    messages.error(request, "Something Went Wrong")
                    return view_blog_user_comment(request, blog_id, user_id)
            else:
                try:
                    if user == 1:
                        comment = BlogComment.objects.get(id=comment_id)
                        comment.delete()
                        messages.success(request, "Deleted")
                        return redirect("view_blog_user", user=int(user_id))
                    else:
                        comment = BlogComment.objects.get(id=comment_id)
                    comment.delete()
                    messages.success(request, "Deleted")
                    return view_blog_user_comment(request, blog_id, user_id)
                except:
                    messages.error(request, "Something Went Wrong")
                    return view_blog_user_comment(request, blog_id, user_id)
        except:
            messages.error(request, "Something Went Wrong")
            return view_blog_user_comment(request, blog_id, user_id)


# Blog User End


# Contact us and user inquiry start
def contact_us_inquiry(request):
    try:
        inquiry = ContactUsInquiry.objects.filter(replied=False).order_by("-id")
        model = Module.objects.all().order_by("id")
        return render(
            request,
            "contact_us_inquiry/inquiry.html",
            {
                "inquiry": inquiry,
                "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request),
            },
        )
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")


def resolved_contact_us_inquiry(request):
    try:
        inquiry_data = ContactUsInquiry.objects.filter(replied = True).order_by("-id")
        model = Module.objects.all().order_by("id")
        return render(request, "contact_us_inquiry/resolved_inquiry.html", {'inquiry_data': inquiry_data, "m": permission(request),
                    "model": model,
                    "module_list": helper(request),
                    "m_check": per(request),})
    except:
        messages.success(request, "Something Went Wrong")
        return redirect("dashboard")

def view_resolved_inquiry(request, id):
    try:
        inquiry = ContactUsInquiry.objects.get(id = id)
        model = Module.objects.all().order_by("id")
        return render(request, "contact_us_inquiry/view_resolved_inquiry.html", {'inquiry': inquiry, "m": permission(request),
                    "model": model,
                    "module_list": helper(request),
                    "m_check": per(request),})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("resolved_contact_us_inquiry")


def delete_resolved_inquiry(request):
    try:
        id = request.POST.get("user_inquiry")
        user_inquiry = ContactUsInquiry.objects.get(id=id)
        user_inquiry.delete()
        messages.success(request, "Deleted")
        return redirect("resolved_contact_us_inquiry")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("resolved_contact_us_inquiry")



def delete_user_inquiry(request):
    try:
        id = request.POST.get("user_inquiry")
        user_inquiry = ContactUsInquiry.objects.get(id=id)
        user_inquiry.delete()
        messages.success(request, "Deleted")
        return redirect("contact_us_inquiry")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("contact_us_inquiry")


def view_user_inquiry(request, id):
    try:
        inquiry = ContactUsInquiry.objects.get(id=id)
        model = Module.objects.all().order_by("id")
        return render(
            request,
            "contact_us_inquiry/view_inquiry.html",
            {
                "inquiry": inquiry,
                "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request),
            },
        )
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("contact_us_inquiry")


def reply_user_inquiry(request):

    try:
        user_id = request.user.id
        user_data = User.objects.get(id = user_id)
        respondent_name= user_data.name
        respondent_email = user_data.email
        id = request.POST.get("reply")
        user = ContactUsInquiry.objects.get(id=id)
        email = user.email
        name = user.name
        reply_text = request.POST.get("editor")
        reply = strip_tags(reply_text)
        if not reply:
            messages.error(request, "Please Enter Message")
            return redirect("view_user_inquiry/" + str(id))
        user.respondent_name = respondent_name
        user.respondent_email = respondent_email
        user.reply = reply
        user.replied_at = timezone.now()
        user.replied = True
        user.save()

        try:
            reply_to_user_inquiry(email, reply_text)
        except:
            pass
        # send_mail(subject, message, from_email, [to], fail_silently=False)
        messages.success(request, "Reply Sent")
        return redirect("contact_us_inquiry")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("contact_us_inquiry")


def contact_us_details(request):
    try:
        contact_us_details = ContactUsDetails.objects.filter(is_delete=False).order_by(
            "-default_address"
        )
        contact_us_details_count = contact_us_details.count()
        model = Module.objects.all().order_by("id")
        return render(
            request,
            "contact_us_inquiry/contact_us_details.html",
            {   "contact_us_details_count": contact_us_details_count, 
                "contact_us_details": contact_us_details,
                "m": permission(request),
                "model": model,
                "module_list": helper(request),
                "m_check": per(request),
            },
        )
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")


def add_contact_us_details(request):
    default_contact_us_details = ContactUsDetails.objects.filter(default_address = True).exists()
    
    if request.method == "POST":
        email = request.POST.get("email").lower()
        mobile = request.POST.get("mobile")
        address = request.POST.get("address")
        if default_contact_us_details:
            default_address = False
        else:
            default_address = True

        ContactUsDetails.objects.create(email=email, mobile=mobile, address=address, default_address = default_address)
        messages.success(request, "Details Saved")
        return redirect("contact_us_details")
        # geolocator = Nominatim(user_agent="adminpanel")
        # location = geolocator.geocode(address)
        # if location:
        #     try:
        #         lat = location.latitude
        #         long = location.longitude
        #         ContactUsDetails.objects.create(
        #             email=email,
        #             mobile=mobile,
        #             address=address,
        #             latitude=lat,
        #             longitude=long,
        #         )
        #         messages.success(request, "Details Saved")
        #         return redirect("contact_us_details")
        #     except:
        #         messages.error(request, "Something Went Wrong")
        #         return redirect("contact_us_details")
        # elif location == None:
            # return render(
            #     request,
            #     "contact_us_inquiry/add_coordinates_details.html",
            #     {"email": email, "mobile": mobile, "address": address},
            # )
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "contact_us_inquiry/add_contact_details.html",
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


def add_coordinates_details(request):
    email = request.POST.get("email").lower()
    mobile = request.POST.get("mobile")
    address = request.POST.get("address")
    lat = request.POST.get("lat")
    long = request.POST.get("long")
    ContactUsDetails.objects.create(
        email=email, mobile=mobile, address=address, latitude=lat, longitude=long
    )
    messages.success(request, "Details Saved")
    return redirect("contact_us_details")


def edit_contact_us_details(request, id):
    contact_us_details = ContactUsDetails.objects.get(id=id)
    if request.method == "POST":
        try:
            details = ContactUsDetails.objects.get(id=id)
            email = request.POST.get("email").lower()
            mobile = request.POST.get("mobile")
            address = request.POST.get("address")
            lat = request.POST.get("lat")
            long = request.POST.get("long")
            details.email = email
            details.address = address
            details.mobile = mobile
            details.latitude = lat
            details.longitude = long
            details.save()
            messages.success(request, "Details Updated")
            return redirect("contact_us_details")
        except:
            messages.error(request, "Something Went Wrong")
            return redirect("contact_us_details")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "contact_us_inquiry/edit_contact_us_details.html",
        {
            "contact_us_details": contact_us_details,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


def delete_contact_us_details(request):
    try:
        id = request.POST.get("contact_details")
        contact_us_details = ContactUsDetails.objects.get(id=id).delete()
        messages.success(request, "Deleted")
        return redirect("contact_us_details")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("contact_us_details")


def default_contact_us_details(request, id):
    try:
        default = ContactUsDetails.objects.get(default_address=True)
        default.default_address = False
        default.save()
    except:
        pass
    try:
        contact_us_details = ContactUsDetails.objects.get(id=id)
        contact_us_details.default_address = True
        contact_us_details.save()
        messages.success(request, "Default Address Changed")
        return redirect("contact_us_details")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("contact_us_details")


# Contact us and user inquiry end   
# newsletter view page and send the mail all the users regarding to dolls news and offers 
@login_required(login_url="login")
def view_newsletter(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method =="POST":
        data = request.POST.get('emailList')
        recipient_list = data.split(',')
        subject = request.POST.get('subject')
        content_html = request.POST.get('message')
        newsletter_mail_to_subscribers(recipient_list, subject, content_html)
        return JsonResponse({'success': True, 'message': 'Mail Sent'})
    model = Module.objects.all().order_by('id')
    newsletter_data = Newsletters.objects.all()
    return render(request,"newsletter/view.html",
    {"newsletterdata": newsletter_data,
    "m": permission(request),
    "model": model,
    "module_list": helper(request),
    "m_check": per(request)})


# admin add the users by the  email-id
@login_required(login_url="login")
def add_newsletter(request):
    if is_normal_user(request):
        return redirect("web_login")
    model = Module.objects.all()
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            Newsletters.objects.create(email=email)

        email_csv = request.FILES.get("email_csv")
        if email_csv:
            import csv
            from io import TextIOWrapper
            email_list = []
            with TextIOWrapper(email_csv, encoding="utf-8") as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    email_list.append(Newsletters(email=row['email address']))
            Newsletters.objects.bulk_create(email_list)

        messages.success(request, "Email Added")
        return redirect("/adminpanel/view_newsletter/")
    return render(
        request,
        "newsletter/add.html",
        {
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_newsletter(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        id = request.POST.get("newsletter")
       
        newsletter = Newsletters.objects.get(id=id)
        newsletter.delete()

        messages.success(request, "Email Deleted")

    return redirect("view_newsletter")


# Contact us and user inquiry end

def delete_link_on_blog(request):
    try:
        id = request.POST.get("delete_link")
        link = LinksOnBlog.objects.get(id=id)
        link.delete()
        messages.success(request, "Deleted")
        return redirect("links_on_blog")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("links_on_bolg")

# Reviews and Rating 
@login_required(login_url="login")
def view_reviews(request):
    if is_normal_user(request):
        return redirect("web_login")
    reviews = Review.objects.all()
    return render(
        request,
        "review-rating/view.html",
        {
            "reviewsdata": reviews,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_reviews_detail(request, id):  # detail page
    if is_normal_user(request):
        return redirect("web_login")
    reviewdetail = Review.objects.get(id=id)
    return render(
        request,
        "review-rating/view_detail.html",
        {
            "reviewdetaildata": reviewdetail,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_reviews(request, id):
    ratting = Review.objects.get(id=id)
    if request.method == "POST":
        rating = request.POST.get("rating")
        review = request.POST.get("review")
        ratting.rating = rating
        ratting.user_review = review
        ratting.save()
        messages.success(request, "Update Successfully Done!!!")
        return redirect("view_reviews")
    return render(
        request,
        "review-rating/edit.html",
        {
            "ratting": ratting,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_reviews(request):
    if is_normal_user(request):
        return redirect("web_login")

    if request.method == "POST":
        id = request.POST.get("review")
        review = Review.objects.get(id=id)
        review.delete()
        messages.success(request, "Reviews  Deleted Successfully")

    return redirect("view_reviews")

#  End Reviews and Rating  

#-----------------------Start Content Management--------------------------------------------#



# Terms&Conditions CURD:
@login_required(login_url="login")
def view_terms(request):
    if is_normal_user(request):
        return redirect("web_login")
    viewterms = TermsCondition.objects.all()
    return render(
        request,
        "conditons/view-terms.html",
        {
            "viewterms": viewterms,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


def add_terms(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            title = request.POST.get("title")

            description = request.POST.get("description")

            if not (
                title
                and not title.isspace()
                and description
                and not description.isspace()
            ):
                messages.error(request, "Both Fileds are Required")
                return redirect("add_terms")

            data = TermsCondition.objects.create(title=title, description=description)
            data.save()
            messages.success(request, "Successfully Added")
            return redirect("view_terms")
    except:
        messages.error(request, "error !!!")
        return redirect("add_terms")

    return render(
        request,
        "conditons/add-terms.html",
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_terms(request, id):
    editterms = TermsCondition.objects.get(id=id)
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        if not title and not description:
            messages.error(request, "Both Fields Required")
            return redirect('edit_terms', id )
        editterms.title = title
        editterms.description = description
        editterms.save()
        messages.success(request, "Update Successfully Done!!!")
        return redirect("view_terms")
    return render(
        request,
        "conditons/edit-terms.html",
        {
            "editterms": editterms,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )

# Privacy CURD:
@login_required(login_url="login")
def view_privacy(request):
    if is_normal_user(request):
        return redirect("web_login")
    viewprivacy = privacy.objects.all()
    return render(
        request,
        "conditons/view-privacy.html",
        {
            "viewprivacy": viewprivacy,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


def add_privacy(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            title = request.POST.get("title")

            description = request.POST.get("description")

            if not (
                title
                and not title.isspace()
                and description
                and not description.isspace()
            ):
                messages.error(request, "Both Fields Required")
                return redirect("add_privacy")

            data = privacy.objects.create(title=title, description=description)
            data.save()
            messages.success(request, "Add Successfully Done!!!")
            return redirect("view_privacy")
    except:
        messages.error(request, "error !!!")
        return redirect("add_privacy")

    return render(
        request,
        "conditons/add-privacy.html",
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_privacy(request, id):
    editprivacy = privacy.objects.get(id=id)
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        editprivacy.title = title
        editprivacy.description = description
        editprivacy.save()
        messages.success(request, "Update Successfully Done!!!")
        return redirect("view_privacy")
    return render(
        request,
        "conditons/edit-privacy.html",
        {
            "editprivacydata": editprivacy,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )

#legal CURD:
@login_required(login_url="login")
def view_legal(request):
    if is_normal_user(request):
        return redirect("web_login")
    viewlegal = Legal.objects.all()
    return render(
        request,
        "conditons/view-legal.html",
        {
            "viewlegal": viewlegal,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


def add_legal(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            title = request.POST.get("title")

            description = request.POST.get("description")

            if not (
                title
                and not title.isspace()
                and description
                and not description.isspace()
            ):
                messages.error(request, "Both Fields Required")
                return redirect("add_legal")

            data = Legal.objects.create(title=title, description=description)
            data.save()
            messages.success(request, "Add Successfully Done!!!")
            return redirect("view_legal")
    except:
        messages.error(request, "error !!!")
        return redirect("add_legal")

    return render(
        request,
        "conditons/add-legal.html",
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_legal(request, id):
    editlegal = Legal.objects.get(id=id)
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        editlegal.title = title
        editlegal.description = description
        editlegal.save()
        messages.success(request, "Update Successfully Done!!!")
        return redirect("view_legal")
    return render(
        request,
        "conditons/edit-legal.html",
        {
            "editlegal": editlegal,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )

# Shipping CURD:
@login_required(login_url="login")
def view_shipping(request):
    if is_normal_user(request):
        return redirect("web_login")
    viewshipping = Shipping.objects.all()
    return render(
        request,
        "conditons/view-shipping.html",
        {
            "viewshipping": viewshipping,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


def add_shipping(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            title = request.POST.get("title")

            description = request.POST.get("description")

            if not (
                title
                and not title.isspace()
                and description
                and not description.isspace()
            ):
                messages.error(request, "Both Fields Required")
                return redirect("add_shipping")

            data = Shipping.objects.create(title=title, description=description)
            data.save()
            messages.success(request, "Add Successfully Done!!!")
            return redirect("view_shipping")
    except:
        messages.error(request, "error !!!")
        return redirect("add_shipping")

    return render(
        request,
        "conditons/add-shipping.html",
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_shipping(request, id):
    editshipping = Shipping.objects.get(id=id)
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        editshipping.title = title
        editshipping.description = description
        editshipping.save()
        messages.success(request, "Update Successfully Done!!!")
        return redirect("view_shipping")
    return render(
        request,
        "conditons/edit-shipping.html",
        {
            "editshippingdata": editshipping,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )

# FAQ CURD:
@login_required(login_url="login")
def view_faq(request):
    if is_normal_user(request):
        return redirect("web_login")
    viewfaq = FAQ.objects.all()
    return render(
        request,
        "conditons/view-FAQ.html",
        {
            "viewfaq": viewfaq,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_faq(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            questions = request.POST.get("question")

            answers = request.POST.get("answer")

            if not (
                questions
                and not questions.isspace()
                and answers
                and not answers.isspace()
            ):
                messages.error(request, "Both Fields Required")
                return redirect("add_faq")

            data = FAQ.objects.create(Questions=questions, Answers=answers)
            data.save()
            messages.success(request, "Add Successfully Done!!!")
            return redirect("view_faq")
    except:
        messages.error(request, "error !!!")
        return redirect("add_faq")

    return render(
        request,
        "conditons/add-FAQ.html",
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_faq(request, id):
    editfaq = FAQ.objects.get(id=id)
    if request.method == "POST":
        question = request.POST.get("question")
        answer = request.POST.get("answer")
        editfaq.Questions = question
        editfaq.Answers = answer
        editfaq.save()
        messages.success(request, "Update Successfully Done !!!!!!")
        return redirect("view_faq")
    return render(request, "conditons/edit-FAQ.html", {
        "editfaq": editfaq,
        "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request),
    })


@login_required(login_url="login")
def view_faq_detail(request, id):
    viewdata = FAQ.objects.get(id=id)
    return render(
        request,
        "conditons/view_FAQ-detail.html",
        {
            "viewdata": viewdata,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_FAQ(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        id = request.POST.get("faq")

        faq = FAQ.objects.get(id=id)
        faq.delete()
    messages.success(request, "FAQ  Deleted Successfully")

    return redirect("view_faq")

#-----------------End Content Management--------------------------#





#----------start Banner Management---------------------#
# Dashboard     Start Slider CURD:
@login_required(login_url="login")
def view_slider(request):
    if is_normal_user(request):
        return redirect("web_login")

    viewdata = Slider.objects.all()

    return render(
        request,
        "banner_management/view_slider.html",
        {
            "viewdata": viewdata,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def add_slider(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            title = request.POST.get("title")
            content = request.POST.get("content")

            image = request.FILES.get("image")

            if not (
                content
                and not content.isspace()
                and image
                and title
                and not title.isspace()
            ):
                messages.error(request, " Filed are Required!!!")
                return redirect("add_slider")
            add_data = Slider.objects.create(content=content, image=image, title=title)
            add_data.save()
            messages.success(request, "Add Successfully Done!!!")
            return redirect("view_slider")

    except:
        messages.error(request, "Add Successfully Not Done!!!")
        return redirect("add_slider")

    return render(
        request,
        "banner_management/add-slider.html",
        {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def edit_slider(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        sliderdata = Slider.objects.get(id=id)
        if request.method == "POST":
            edit_title = request.POST.get("title")
            edit_content = request.POST.get("content")
            edit_image = request.FILES.get("image")
            if edit_image:
                sliderdata.image = edit_image

            sliderdata.content = edit_content
            sliderdata.title = edit_title
            sliderdata.save()
            messages.success(request, "Update Successfully Done!!!!")
            return redirect("view_slider")

    except:
        messages.error(request, "Update  Not Successfully Done!!!!")
        return redirect("edit_slider")

    return render(
        request,
        "banner_management/edit-slider.html",
        {
            "slider_data": sliderdata,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_slider_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    view_detail = Slider.objects.get(id=id)
    return render(
        request,
        "banner_management/view-detail-slider.html",
        {
            "view_detaildata": view_detail,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def delete_slider(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        id = request.POST.get("slider")

        slider = Slider.objects.get(id=id)
        slider.delete()
    messages.success(request, "slider  Deleted Successfully")
    return redirect("view_slider")
# End Slider CURD


# Dashboard Start product shop CURD
@login_required(login_url="login")
def view_product_shop(request):
    if is_normal_user(request):
        return redirect("web_login")
    
    viewdata = ProductShop.objects.all()
    
    return render(
        request,
        "banner_management/product-shop/view.html",
        {
            "viewdata": viewdata,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


# @login_required(login_url="login")
# def add_product_shop(request):
#     if is_normal_user(request):
#         return redirect("web_login")
    
#     try:
#         if request.method == "POST":
#             title = request.POST.get("title")
#             content = request.POST.get("content")
#             image = request.FILES.get("image")
            
#             if not ( content and not content.isspace() and image and title and not title.isspace()):
#                 messages.error(request, " Fileds are Required!!!")
#                 return redirect("add_product_shop")
            
#             ProductShop.objects.create(content=content, image=image, title=title)
#             messages.success(request, "Add Successfully Done!!!")
#             return redirect("view_product_shop")

#     except:
#         messages.error(request, "Add Successfully Not Done!!!")
#         return redirect("add_product_shop")

#     return render(
#         request,
#         "banner_management/product-shop/add.html",
#         {
#             "m": permission(request),
#             "module_list": helper(request),
#             "m_check": per(request),
#         },
#     )


@login_required(login_url="login")
def edit_product_shop(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    
    try:
        product_shop_data = ProductShop.objects.get(id=id)
        if request.method == "POST":
            edit_title = request.POST.get("title")
            edit_content = request.POST.get("content")
            edit_image = request.FILES.get("image")
            
            if edit_image:
                product_shop_data.image = edit_image
                
            product_shop_data.title = edit_title
            product_shop_data.content = edit_content
            product_shop_data.save()
            messages.success(request, "Update Successfully")
            return redirect("view_product_shop")

    except:
        messages.error(request, "Failed To Update")
        return redirect("edit_product_shop")

    return render(
        request,
        "banner_management/product-shop/edit.html",
        {
            "product_shop": product_shop_data,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_product_shop_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    
    view_detail = ProductShop.objects.get(id=id)
    
    return render(
        request,
        "banner_management/product-shop/view-detail.html",
        {
            "view_detaildata": view_detail,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


# @login_required(login_url="login")
# def delete_product_shop(request):
#     if is_normal_user(request):
#         return redirect("web_login")
    
#     if request.method == "POST":
#         id = request.POST.get("product_shop")
#         product_shop = ProductShop.objects.get(id=id)
#         product_shop.delete()
#     messages.success(request, "Deleted Successfully")
#     return redirect("view_product_shop")

# End product shop CURD

#  Dashboard Start Subscription CURD
@login_required(login_url="login")
def view_subscription(request):
    if is_normal_user(request):
        return redirect("web_login")
    
    viewdata_subscription = Subscription.objects.all()
    
    return render(
        request,
        "banner_management/subscription/view.html",
        {
            "viewdata_sub": viewdata_subscription,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )

# to change home page subscription section title, image, content 
# @login_required(login_url="login")
# def add_subscription(request):
#     if is_normal_user(request):
#         return redirect("web_login")

#     try:
#         if request.method == "POST":
#             title = request.POST.get("title")
#             content = request.POST.get("content")
#             image = request.FILES.get("image")

#             if not (
#                 content
#                 and not content.isspace()
#                 and image
#                 and title
#                 and not title.isspace()
#             ):
#                 messages.error(request, " Fileds are Required!!!")
#                 return redirect("add_subscription")
            
#             Subscription.objects.create(
#                 title=title, content=content, image=image
#             )
#             messages.success(request, "Subscription Add successfully Done!!!!")
#             return redirect("view_subscription")
#     except:
#         messages.error(request, "Add Successfully Not Done!!!")
#         return redirect("add_subscription")

#     return render(
#         request,
#         "banner_management/subscription/add.html",
#         {
#             "m": permission(request),
#             "module_list": helper(request),
#             "m_check": per(request),
#         },
#     )

# to update home page subscription section title, image, content
@login_required(login_url="login")
def edit_subscription(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    
    try:
        subscription_data = Subscription.objects.get(id=id)
        if request.method == "POST":
            edit_title = request.POST.get("title")
            edit_content = request.POST.get("content")
            edit_image = request.FILES.get("image")
            if edit_image:
                subscription_data.image = edit_image
            subscription_data.title = edit_title
            subscription_data.content = edit_content
            subscription_data.save()
            messages.success(request, "Update Successfully Done!!!!")
            return redirect("view_subscription")

    except:
        messages.error(request, "Update  Not Successfully Done!!!!")
        return redirect("edit_subscription", id)

    return render(
        request,
        "banner_management/subscription/edit.html",
        {
            "subscription_data": subscription_data,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_detail_subscription(request, id): # detail page
    if is_normal_user(request):
        return redirect("web_login")
    view_detail = Subscription.objects.get(id=id)
    return render(
        request,
        "banner_management/subscription/view-detail.html",
        {
            "view_detaildata": view_detail,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


# @login_required(login_url="login")
# def delete_subscription(request):

#     if is_normal_user(request):
#         return redirect("web_login")
#     if request.method == "POST":
#         id = request.POST.get("subscription")

#         subscription = Subscription.objects.get(id=id)
#         subscription.delete()
#         messages.success(request, "Subscription data Deleted Successfully!!!!!")
#     return redirect("view_subscription")

#End subscription 

# Dashboard product imagine CURD 
@login_required(login_url="login")
def view_product_imagine(request):
    if is_normal_user(request):
        return redirect("web_login")
    view_data = ProductImagine.objects.all()
    return render(
        request,
        "banner_management/product-imagine/view.html",
        {
            "viewdata": view_data,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


# @login_required(login_url="login")
# def add_product_imagine(request):
#     if is_normal_user(request):
#         return redirect("web_login")
#     try:
#         if request.method == "POST":
#             title = request.POST.get("title")
#             content = request.POST.get("content")
#             image = request.FILES.get("image")
#             if not (
#                 title
#                 and not title.isspace()
#                 and image
#                 and content
#                 and not content.isspace()
#             ):
#                 messages.error(request, "Fields  are required ")
#                 return redirect("add_product_imagine")
#             add_data = ProductImagine.objects.create(
#                 title=title, content=content, image=image
#             )
#             add_data.save()
#             messages.success(request, "Add succcessfully Done !!!!")
#             return redirect("view_product_imagine")
#     except:
#         messages.error(request, "Add succcessfully Not Done !!!!")
#         return redirect("add_product_imagine")
#     return render(
#         request,
#         "banner_management/product-imagine/add.html",
#         {
#             "data": request.POST,
#             "m": permission(request),
#             "module_list": helper(request),
#             "m_check": per(request),
#         },
#     )


@login_required(login_url="login")
def edit_product_imagine(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        product_imagine_data = ProductImagine.objects.get(id=id)
        if request.method == "POST":
            edit_title = request.POST.get("title")

            edit_content = request.POST.get("content")
            edit_image = request.FILES.get("image")
            if edit_image:
                product_imagine_data.image = edit_image
            product_imagine_data.title = edit_title
            product_imagine_data.content = edit_content
            product_imagine_data.save()
            messages.success(request, "Update Successfully Done!!!!")
            return redirect("view_product_imagine")

    except:
        messages.error(request, "Update  Not Successfully Done!!!!")
        return redirect("edit_product_imagine")

    return render(
        request,
        "banner_management/product-imagine/edit.html",
        {
            "product_imagine": product_imagine_data,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def view_product_imagine_detail(request, id):# particular product detail page 
    if is_normal_user(request):
        return redirect("web_login")
    view_detail = ProductImagine.objects.get(id=id)
    return render(
        request,
        "banner_management/product-imagine/view-detail.html",
        {
            "view_detaildata": view_detail,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


# @login_required(login_url="login")
# def delete_product_imagine(request):
#     if is_normal_user(request):
#         return redirect("web_login")
#     if request.method == "POST":
#         id = request.POST.get("product_imagine")

#         product_imagine = ProductImagine.objects.get(id=id)
#         product_imagine.delete()
#         messages.success(request, "product imagine data Deleted Successfully!!!!!")
#     return redirect("view_product_imagine")


# End product imagine curd 
#-------------------------------------End Banner Management------------------------#


# Start Offer Management
@login_required(login_url="login")
def offer_view(request):
    if is_normal_user(request):
        return redirect("web_login")
    offer_data = Offer.objects.all()

    return render(
        request,
        "offer_management/view_offer.html",
        {
            "offer_data": offer_data,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def offer_add(request):
    if is_normal_user(request):
        return redirect("web_login")

    subcat = SubCategory.objects.filter(category_id=1)
    try:
        if request.method == "POST":
            name = request.POST.get("name")

            percentage = request.POST.get("percentage")

            subcategory = [1, 2, 3]  # request.POST.get('subcategory')
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")

            status = request.POST.get("is_active")

            if not (
                name
                and not name.isspace()
                and percentage
                and not percentage.isspace()
                # subcategory and not subcategory.isspace()
                and status
                and not status.isspace()
                and start_date
                and not start_date.isspace()
                and end_date
                and not end_date.isspace()
            ):

                messages.error(request, " All Fields  are required ")
                return redirect("offer_add")
            offer_add = Offer.objects.create(
                name=name,
                percentage=percentage,
                is_active=status,
                subcategory=subcategory,
                start_date=start_date,
                end_date=end_date,
            )
            offer_add.save()
            messages.success(request, "Add succcessfully Done !!!!")
            return redirect("offer_view")
    except:

        messages.error(request, "Add succcessfully Not Done !!!!")
        return redirect("offer_add")

    return render(
        request,
        "offer_management/add_offer.html",
        {
            "subcategory_data": subcat,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )


@login_required(login_url="login")
def offer_edit(request, id):
    if is_normal_user(request):
        return redirect("web_login")

    subcat = SubCategory.objects.filter(category_id=1)
    try:
        edit_data = Offer.objects.get(id=id)
        if request.method == "POST":
            edit_name = request.POST.get("name")
            edit_percentage = request.POST.get("percentage")

            edit_start_date = request.POST.get("start_date")
            edit_end_date = request.POST.get("end_date")
            # edit_subcategory=request.POST.get('subcategory')
            edit_status = request.POST.get("is_active")

            edit_data.name = edit_name
            edit_data.percentage = edit_percentage
            edit_data.start_date = edit_start_date
            edit_data.end_date = edit_end_date
            # edit_data.subcategory=edit_subcategory
            edit_data.is_active = edit_status

            edit_data.save()
            messages.success(request, "Update Successfully Done!!!!")
            return redirect("offer_view")

    except:
        messages.success(request, "Update Not Done Successfully !!!!")
        return redirect("offer_edit")

    return render(request,'offer_management/edit_offer.html',
                {'edit_data':edit_data,
                 "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request),

                 })
        
@login_required(login_url="login")
def offer_view_detail(request,id):
    if is_normal_user(request):
        return redirect("web_login")
    view_detail = Offer.objects.get(id=id)
    return render(
        request,
        "offer_management/view_detail_offer.html",
        {
            "view_detaildata": view_detail,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        },
    )

@login_required(login_url="login")
def offer_delete(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        id = request.POST.get("offer")

        offer = Offer.objects.get(id=id)
        offer.delete()
        messages.success(request, " Offer data Deleted Successfully!!!!!")
    return redirect("offer_view")
# End Offer Management#



# links on blog start
# to show links on blog
@login_required(login_url="login")
def links_on_blog(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        links_data = LinksOnBlog.objects.filter(is_social = False)

        return render(request, "blog_management/links_on_blog/links.html", {"links": links_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")  


# to add link on blog
@login_required(login_url="login")
def add_links_on_blog(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            title = request.POST.get("title")
            image = request.FILES.get("image")
            url = request.POST.get("url")
            status = request.POST.get("is_active")
            if LinksOnBlog.objects.filter(url=url).exists():
                messages.error(request, "URL Already Exist")
                return redirect("add_links_on_blog")
            LinksOnBlog.objects.create(title=title, image=image, url=url, is_active=status, is_social = False)# here "is_social" is False to make this link custom link
            messages.success(request, "Link Added")
            return redirect("links_on_blog")
        return render(request, "blog_management/links_on_blog/add.html", {"m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),} )
    except:
        messages.error(request, "Something Went wrong")
        return redirect("links_on_blog")


# to delete link on blog
@login_required(login_url="login")
def delete_link_on_blog(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("delete_link")
        link = LinksOnBlog.objects.get(id=id)
        link.delete()
        messages.success(request, "Deleted")
        return redirect("links_on_blog") 
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("links_on_bolg")


# to edit links on blog
@login_required(login_url="login")
def edit_links_on_blog(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        links_data = LinksOnBlog.objects.get(id=id)
        if request.method == "POST":
            new_title = request.POST.get("title")
            new_image = request.FILES.get("image")
            new_url = request.POST.get("url")
            new_status = request.POST.get("is_active")
            links_data.title = new_title
            try: 
                if new_image:
                    links_data.image = new_image
                links_data.url = new_url
                links_data.is_active = new_status
                links_data.save()
                messages.success(request, "Link Updated")
                return redirect("links_on_blog")
            except:
                messages.error(request, "Something Went Wrong")    
        return render(request, "blog_management/links_on_blog/edit.html",  {"links": links_data,"m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.error(request, "Something Went wrong")
        return redirect("links_on_blog")

# links on blog end  
@login_required(login_url="login")
def social_media_link(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        social_link = LinksOnBlog.objects.filter(is_social = True)
        return render(request, "blog_management/links_on_blog/social_link.html", {"links": social_link,"m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")

# to add social media link
@login_required(login_url="login")
def add_social_media_link(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            title = request.POST.get("title")
            image = request.FILES.get("image")
            url = request.POST.get("url")
            status = request.POST.get("is_active")
            if LinksOnBlog.objects.filter(url=url).exists():
                messages.error(request, "URL Already Exist")
                return redirect("add_social_media_link")
            LinksOnBlog.objects.create(title=title, image=image,
             url=url, is_active=status, is_social = True)# here "is_social" is true to make this link social media link
            messages.success(request, "Link Added")
            return redirect("social_media_link")
        return render(request, "blog_management/links_on_blog/add_social.html", {"m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),} )
    except:
        messages.error(request, "Something Went wrong")
        return redirect("social_media_link")

# to delete social media link
@login_required(login_url="login")
def delete_social_media_link(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("delete_link")
        link = LinksOnBlog.objects.get(id=id)
        link.delete()
        messages.success(request, "Deleted")
        return redirect("social_media_link") 
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("social_media_link")


# to edit social media link
@login_required(login_url="login")
def edit_social_media_link(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        social_link = LinksOnBlog.objects.get(id=id)
        if request.method == "POST":
            new_title = request.POST.get("title")
            new_image = request.FILES.get("image")
            new_url = request.POST.get("url")
            new_status = request.POST.get("is_active")
            social_link.title = new_title
            try: 
                if new_image:
                    social_link.image = new_image
                social_link.url = new_url
                social_link.is_active = new_status
                social_link.save()
                messages.success(request, "Link Updated")
                return redirect("social_media_link")
            except:
                messages.error(request, "Something Went Wrong")
                return render(request, "blog_management/links_on_blog/edit_social.html", {"links": social_link,"m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})  
        return render(request, "blog_management/links_on_blog/edit_social.html", {"links": social_link})
    except:
        messages.error(request, "Something Went wrong")
        return redirect("social_media_link")
# links on blog end


# order management start
# to show order
def order_management(request):
    if is_normal_user(request):
        return redirect("web_login")
    orders_data = ProductOrder.objects.select_related('user','shipping_address').filter(listing = True).order_by("-id")
    # orders_data = ProductOrder.objects.filter(listing = True).order_by("-id")
    model = Module.objects.all().order_by("id")
    return render(
        request,
        "order_management/orders.html",
        {
            "orders": orders_data,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request),
        },
    )

def delete_order_listing(request):
    if is_normal_user(request):
        return redirect("web_login")
    order = request.POST.get("order_id")
    order_data = ProductOrder.objects.get(id = order)
    order_data.listing = False
    order_data.save()
    messages.success(request, "Order Record Deleted")
    return redirect('order_management') 

# to show details of order
@login_required(login_url="login")
def view_order(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    product_data = ProductOrderData.objects.filter(product_order_id = id)
    orders_data = ProductOrder.objects.get(id = id)
    product_image = ShopProductImage.objects.all()   

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
    total_quantity = sum(quantity)

    if orders_data.offer_id:
        offer_data = Offer.objects.get(id = orders_data.offer_id)
        price_after_offer = (product_offer_price * offer_data.percentage)/100
        total_savings = product_original_price - price_after_offer
    else:
        offer_data = None
        total_savings = product_original_price - product_offer_price
        price_after_offer = None

    model = Module.objects.all().order_by("id")
    return render(request, 'order_management/view_order.html', 
        {   "price_after_offer": price_after_offer,
            "offer_data": offer_data,
            "total_quantity": total_quantity,
            "product_offer_price": product_offer_price,
            "product_original_price": product_original_price,
            "total_savings": total_savings,
            "product_image": product_image,
            "orders": orders_data,
            "product_data": product_data,
            "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request)}
        )

def cancel_order(request):
    if is_normal_user(request):
        return redirect("web_login")
    id = request.POST.get("order_id")
    orders_data = ProductOrder.objects.get(id = id)
    order_id = orders_data.order_id
    product_data = ProductOrderData.objects.filter(product_order_id = id)
    for product in product_data:
        order_product_id = product.shop_product_id
        shop_product = ShopProduct.objects.get(id = order_product_id)
        shop_product.quantity += product.quantity
        shop_product.save()
    orders_data.order_status = "Canceled"
    time = timezone.now()
    orders_data.canceled_at = time
    orders_data.canceled_by = "Admin"
    orders_data.save()
    user_id = orders_data.user_id
    user_data = User.objects.get(id = user_id)
    name = user_data.name
    email = user_data.email
    try:
        admin_canceled_order_mail(name, email, order_id, time)
    except:
        pass
    messages.success(request, "Order Canceled")
    return redirect("order_management")


# when order cancelled this function is used to refund the amount which paid from wallet and from stripe
def refund_to_customer(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    product_order = ProductOrder.objects.filter(id=id)
    if not product_order:
        messages.error(request, "Order Not Found")
        return redirect('order_management')
    
    product_order = product_order.last()
    if product_order.order_status == 'Canceled' and product_order.is_refunded:
        messages.error(request, "Order Already Cancelled and Amount Refunded to Customer")
        return redirect('order_management')

    if request.method == 'POST':
        wallet_amount = float(request.POST.get('wallet_amount', 0))
        stripe_amount = float(request.POST.get('stripe_amount', 0))

        paid_by_stripe = float(product_order.paid_by_stripe)

        if paid_by_stripe > 0:
            order_detail = OrderDetail.objects.filter(product_order_id=id, user_id=product_order.user_id).last()

            if not order_detail:
                messages.error(request, "Order Not Found")
                return redirect('order_management')

            if stripe_amount > paid_by_stripe:
                messages.error(request, f"You cannot refund more than ${paid_by_stripe}")
                return redirect('refund_to_customer', id)
            
            try:
                refund_response = create_refund(order_detail.stripe_charge_id, int(stripe_amount * 100))
            except:
                messages.error(request, "Already Refunded")
                return redirect('order_management')
            
            if refund_response.get("status") != "succeeded":
                messages.error(request, "Refund Failed")
                return redirect('refund_to_customer', id)

        user = product_order.user
        if float(product_order.paid_by_wallet) > 0:
            product_order.user.wallet = float(user.wallet) + wallet_amount
            user.save()

        product_order.is_refunded = True
        product_order.order_status = "Canceled"
        product_order.canceled_by = "Admin"
        product_order.canceled_at = datetime.now()
        product_order.save()

        admin_refund_amount_to_wallet_order_mail(user.email, product_order.order_id, datetime.now())

        messages.success(request, "Amount Refunded to Customer")
        return redirect('order_management')

    return render(request, 'order_management/edit-order.html', {
        'product_order': product_order,
        "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request)
    })
       

# order management end    

# Gift card Price and expiry days list 
@login_required(login_url="login")
def giftcard_view(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        giftcard_data=GiftCard.objects.all()
        return render(
            request,
            'gift_card/giftcard_view.html',
            {
                'giftcard_data':giftcard_data,
                "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request),
            }
        )
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('dashboard')

# Gift card Price and expiry days Add
@login_required(login_url="login")
def giftcard_add(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method=="POST":
            gift_price = request.POST.get('gift_price')
            days_of_expire = request.POST.get('days_of_expire')
    
            if not (gift_price and not gift_price.isspace() and days_of_expire and not days_of_expire.isspace() ):
                messages.error(request,'Both Fields Are Required!!!')
                return redirect('giftcard_add')
            
            card = GiftCard.objects.create(gift_price=gift_price, days=days_of_expire)
            
            messages.success(request,'Gift Card Added Successfully Done!!!')
            return redirect('giftcard_view')
    except:
        messages.error(request, "Something Went wrong")
        return redirect("giftcard_add")
    
    return render(request,'gift_card/giftcard_add.html', {"m": permission(request),
        "module_list": helper(request),
        "m_check": per(request),
    })
    



# User Gift Card used or not used in this list:
@login_required(login_url="login")
def view_user_gift_card(request):
    if is_normal_user(request):
        return redirect("web_login")
    data = UserGiftCard.objects.all()
    return render(
        request,
        'gift_card/user_gift_card_view.html',
        {
            'data':data,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        }
    )


def add_giftcard_type(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        giftcard_type = request.POST.get("giftcard_type")
        status = request.POST.get('is_active')
        GiftCardType.objects.create(giftcard_type=giftcard_type, is_active=status)
        messages.success(request, "Added")
        return redirect('giftcard_type')
    return render(request, 'giftcard_type/add_giftcard_type.html', {"m": permission(request),
        "module_list": helper(request),
        "m_check": per(request),
    })


def giftcard_type(request):
    if is_normal_user(request):
        return redirect("web_login")
    giftcard_types = GiftCardType.objects.all()
    return render(request, 'giftcard_type/giftcard_type.html', {"giftcard_types": giftcard_types, "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request)})


def edit_giftcard_type(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    giftcard_type_data = GiftCardType.objects.get(id=id)
    if request.method == "POST":
        giftcard_type = request.POST.get('giftcard_type')
        status = request.POST.get('is_active')
        giftcard_type_data.giftcard_type = giftcard_type
        giftcard_type_data.is_active = status
        giftcard_type_data.save()
        messages.success(request, "Edited")
        return redirect('giftcard_type')
    return render(request, 'giftcard_type/edit_giftcard_type.html', {"giftcard_type": giftcard_type_data, "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request)})


def delete_giftcard_type(request):
    if is_normal_user(request):
        return redirect("web_login")
    id = request.POST.get("delete_giftcard_type")
    GiftCardType.objects.get(id=id).delete()
    messages.success(request, "Deleted")
    return redirect('giftcard_type')

# Subscriptions Start
@login_required(login_url="login")
def subscription_plan(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subscriptions = SubscriptionPlan.objects.all().order_by("-id")
        data = {
            'subscriptions': subscriptions,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        }
        return render(request, 'subscription_management/subscription.html', data)
    except Exception as err:
        messages.error(request, "Something Went Wrong")    
        return redirect('dashboard')


# to show subscription plan
@login_required(login_url="login")
def view_subscription_plan(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subscriptions = SubscriptionPlan.objects.get(id=id)
        benefits = SubscriptionPlanAndBenefits.objects.filter(plan_id = id)
        return render(request, 'subscription_management/view_subscription_plan.html', {'subscriptions': subscriptions, "benefits": benefits, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except Exception as err:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription_plan')

# to add subscription plan
@login_required(login_url="login")
def add_subscription_plan(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subscription_benefit = SubscriptionPlanBenefits.objects.filter(is_active = True)
        if request.method == "POST":
            subscription_type = request.POST.get("subscription_type")
            original_price = request.POST.get("original_price")
            offer_price = float(request.POST.get("offer_price"))
            # status = request.POST.get("is_active")
            benefits = request.POST.getlist("subscription_benefit")
            description = request.POST.get('description')
            
            plan = create_product(subscription_type, description)
            
            interval_count = interval_dict.get(subscription_type)
            recurring = {"interval": "month", "interval_count": interval_count}
            if offer_price > 0:
                subscription_price = offer_price
            else:
                subscription_price = original_price
                
            amount = int(float(subscription_price) * 100)
            subscription_price_obj = create_subscription_price(amount=amount, recurring=recurring, stripe_product_id=plan.id)
            
            if SubscriptionPlan.objects.filter(plan_type=subscription_type).exists():
                old_subscription_plan = SubscriptionPlan.objects.filter(plan_type=subscription_type).last()
                old_subscription_plan.is_active = False
                old_subscription_plan.save()

            sort_order = {
                'Monthly': 1,
                'Quarterly': 2,
                'Bi-Annual': 3,
                'Annual': 4
            }
                
            subscription = SubscriptionPlan.objects.create(plan_type=subscription_type, original_price=original_price, offer_price=offer_price, subscription_price_id=subscription_price_obj.id, plan_id=plan.id, sort_order=sort_order.get(subscription_type, None))
            
            for id in benefits:
                benefit = int(id)
                SubscriptionPlanAndBenefits.objects.create(plan_id=subscription.id, benefit_id=benefit)
            messages.success(request, "Subscription Plan Added")
            return redirect ('add_subscription_plan')
        return render(request, 'subscription_management/add_subscription.html', {'subscription_benefit': subscription_benefit, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})   
    except Exception as err:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription_plan')

@login_required(login_url="login")
# to edit subscription plan
def edit_subscription_plan(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subscription = SubscriptionPlan.objects.get(id=id)
        subscription_id = subscription.id
        subscription_benefit = SubscriptionPlanBenefits.objects.filter(is_active = True)
        subscription_and_benefit = SubscriptionPlanAndBenefits.objects.filter(plan_id = id)
        benefit_list = []
        for benefit in subscription_and_benefit:
            id = benefit.benefit_id
            benefit_list.append(id)
        if request.method == "POST":
            subscription_and_benefit.delete()
            # subscription_type = request.POST.get("subscription_type")
            # original_price = request.POST.get("original_price")
            # offer_price = request.POST.get("offer_price")
            status = request.POST.get("is_active")
            benefits = request.POST.getlist("subscription_benefit")
            # description = request.POST.get('description')
            
            
            # plan = update_product(subscription.plan_id, name=subscription_type, description=description)
            
            # interval_count = interval_dict.get(subscription_type)
            # recurring = {"interval": "month", "interval_count": interval_count}
            # amount = int(float(offer_price) * 100)
            # subscription_price_obj = update_subscription_price(subscription_price_id=subscription.subscription_price_id, amount=amount, recurring=recurring, stripe_product_id=plan.id)
            
            # subscription.plan_type = subscription_type 
            # subscription.original_price = original_price
            # subscription.offer_price = offer_price
            subscription.is_active = status
            subscription.save()
            for benefit_id in benefits:
                benefit = int(benefit_id)
                SubscriptionPlanAndBenefits.objects.create(plan_id=subscription_id, benefit_id=benefit)
            messages.success(request, "Subscription Plan Updated")
            return redirect("subscription_plan") 
        return render(request, 'subscription_management/edit_subscription_plan.html', {'subscription': subscription, 'subscription_benefit': subscription_benefit, 'benefit_list': benefit_list, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)}) 
    except Exception as err:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription_plan')

@login_required(login_url="login")
# to delete subscription plan
def delete_subscription_plan(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("delete_subscription")          
        subscription = SubscriptionPlan.objects.get(id=id)
        delete_product(subscription.plan_id)
        subscription.delete()
        messages.success(request, "Subscription Deleted")
        return redirect("subscription_plan")
    except Exception as err:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription_plan')

def shero_subscribers(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subscribers_data = UserSubscriberHistory.objects.values('user_id').annotate(max_id=Max('id'))
        subscribers = []
        i = 0
        while i < len(subscribers_data):
            subscriber = UserSubscriberHistory.objects.get(id = subscribers_data[i]["max_id"])
            subscribers.append(subscriber)
            i += 1
        return render(request, "subscription_management/shero_subscribers.html", {"subscribers": subscribers, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")

def view_subscriber_details(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subscribers_history = UserSubscriberHistory.objects.filter(user_id = id).order_by("-id")
        return render(request, "subscription_management/view_shero_subscriber.html", {"subscribers_history": subscribers_history, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("shero_subscribers")


def delete_shero_subscribers(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("subscriber")
        subscriber = UserSubscriptions.objects.get(id = id)
        subscriber.is_delete = True
        subscriber.save()
        messages.success(request, "Deleted")
        return redirect (shero_subscribers)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("shero_subscribers")

# to show subscription benefits
@login_required(login_url="login")
def subscription_benefit(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        subscription_benefit = SubscriptionPlanBenefits.objects.all()
        data = {
            "subscription_benefit": subscription_benefit,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        }
        return render(request, 'subscription_management/subscription_benefit.html', data)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('dashboard')
        

# to add subscription benefit
@login_required(login_url="login")
def add_subscription_benefit(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        data = {
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
            }
        if request.method == "POST":
            subscription_benefit = request.POST.get("subscription_benefit")
            status = request.POST.get("is_active")
            SubscriptionPlanBenefits.objects.create(title=subscription_benefit, is_active=status)
            messages.success(request, "Subscription Benefit Added")
            return redirect ('add_subscription_benefit')
        return render(request, 'subscription_management/add_subscription_benefit.html', data)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription_benefit')


@login_required(login_url="login")
# to edit subscription benefit
def edit_subscription_benefit(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try: 
        subscription_benefit = SubscriptionPlanBenefits.objects.get(id=id)
        if request.method == "POST":
            subscription_benefit_title = request.POST.get("subscription_benefit_title")
            status = request.POST.get("is_active")
            subscription_benefit.title = subscription_benefit_title 
            subscription_benefit.is_active = status
            subscription_benefit.save()
            messages.success(request, "Subscription Benefit Updated")
            return redirect("subscription_benefit") 
        return render(request, 'subscription_management/edit_subscription_benefit.html', {'subscription_benefit': subscription_benefit, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request) }) 
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription_benefit')


@login_required(login_url="login")
# to delete subscription benefit
def delete_subscription_benefit(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("delete_subscription_benefit")
        SubscriptionPlanBenefits.objects.get(id=id).delete()
        messages.success(request, "Subscription Benefit Deleted")
        return redirect("subscription_benefit")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('subscription_benefit')    

# Subscriptions End


# Shero Dolls Start
@login_required(login_url="login")
def shero_dolls(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        shero_dolls = SheroDollsImage.objects.all().order_by("-id")
        return render(request, "shero_dolls_management/shero_dolls.html", {
            "shero_dolls": shero_dolls,
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request),
        })
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('dashboard') 
            
# to add new shero doll
@login_required(login_url="login")
def add_shero_dolls(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        countries = Country.objects.filter(is_active=True)
        months_list = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
        current_datetime = datetime.now()
        years_list = (current_datetime.year, current_datetime.year-1)
        if request.method == "POST":
            name = request.POST.get("name")
            month = request.POST.get("month")
            year = request.POST.get("year") 
            claim_to_fame = request.POST.get("claim_to_fame")
            original_price = request.POST.get("original_price")
            offer_price = request.POST.get("offer_price")
            quantity = request.POST.get("quantity")
            country = request.POST.get("country")
            og_title = request.POST.get("og_title")
            og_description = request.POST.get("og_description")
            status = request.POST.get("status")
            description = request.POST.get("editor")
            features = request.POST.get("features")
            primary_image = request.FILES.get("primary_image")
            og_image = request.FILES.get("og_image")
            shero_dolls_images = request.FILES.getlist("shero_dolls_images")
            offer_price = 0
            shero_dolls = SheroDolls.objects.create(
                og_title = og_title, og_description = og_description,
                name=name, month=month, year=year, slug=slugify(name),
                original_price = original_price, offer_price = offer_price, 
                country_id=country, is_active = status, quantity = quantity, 
                claim_to_fame=claim_to_fame, features=features, description = description
            )
            shero_dolls_id = shero_dolls.id
            shero_dolls_image = SheroDollsImage.objects.create(  shero_dolls_id = shero_dolls_id, primary_img = primary_image, og_img = og_image)
            for i in range(0, len(shero_dolls_images)):
                    SheroDollsImageSubTable.objects.create(
                        shero_dolls_image_id=shero_dolls_image.id, images=shero_dolls_images[i]
                    )
            messages.success(request, "Shero Doll Added")
            return redirect('shero_dolls')

        return render(request, "shero_dolls_management/add_shero_dolls.html", {"countries": countries, "months_list": months_list, "years_list": years_list, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('shero_dolls')

# to delete shero dolls
@login_required(login_url="login")
def delete_shero_dolls(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("delete_shero")
        shero_dolls = SheroDolls.objects.get(id=id).delete()
        messages.success(request, "Shero Doll Deleted")
        return redirect("shero_dolls")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('shero_dolls')



@login_required(login_url="login")
# to edit shero dolls details
def edit_shero_dolls(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        months_list = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
        current_datetime = datetime.now()
        years_list = (current_datetime.year, current_datetime.year-1)
        countries = Country.objects.filter(is_active=True)
        shero_dolls = SheroDollsImage.objects.get(id=id)
        shero_dolls_image = SheroDollsImageSubTable.objects.filter(shero_dolls_image_id=id)
        if request.method == "POST":
            name = request.POST.get("name")
            month = request.POST.get("month")
            year = request.POST.get("year")
            claim_to_fame = request.POST.get("claim_to_fame")
            original_price = request.POST.get("original_price")
            offer_price = request.POST.get("offer_price")
            quantity = request.POST.get("quantity")
            og_title = request.POST.get("og_title")
            og_description = request.POST.get("og_description")
            country = request.POST.get("country")
            status = request.POST.get("status")
            description = request.POST.get("editor")
            features = request.POST.get("features")
            primary_image = request.FILES.get("primary_image")
            og_image = request.FILES.get("og_image")
            shero_dolls_images = request.FILES.getlist("shero_dolls_images")
            offer_price = 0
            shero_dolls.shero_dolls.name = name
            shero_dolls.slug = slugify(name)
            shero_dolls.shero_dolls.month = month
            shero_dolls.shero_dolls.year = year
            shero_dolls.shero_dolls.original_price = original_price
            shero_dolls.shero_dolls.offer_price = offer_price
            shero_dolls.shero_dolls.quantity = quantity
            shero_dolls.shero_dolls.country_id = country
            shero_dolls.shero_dolls.claim_to_fame = claim_to_fame
            shero_dolls.shero_dolls.is_active = status
            shero_dolls.shero_dolls.description = description
            shero_dolls.shero_dolls.og_title = og_title
            shero_dolls.shero_dolls.og_description = og_description
            shero_dolls.shero_dolls.features = features
            shero_dolls.shero_dolls.save()
            if primary_image:
                shero_dolls.primary_img = primary_image
            if og_image:
                shero_dolls.og_img = og_image

            shero_dolls.save()

            i = 1
            j = 5 - shero_dolls_image.count()
            for img in shero_dolls_images:
                if i > j:
                    break
                SheroDollsImageSubTable.objects.create(
                    images=img, shero_dolls_image_id=shero_dolls.id
                )
                i += 1

            messages.success(request, "Shero Doll Edited")
            return redirect("shero_dolls")

        return render(request, "shero_dolls_management/edit_shero_dolls.html", {"shero_dolls": shero_dolls, "shero_dolls_image": shero_dolls_image, "countries": countries, "months_list": months_list,"m": permission(request),
        "module_list": helper(request), "m_check": per(request), "years_list": years_list})   
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('shero_dolls')


@login_required(login_url="login")
@csrf_exempt
def delete_shero_dolls_images(request):
    if is_normal_user(request):
        return redirect("web_login")
    id = request.POST.get("shero_dolls_image")
    SheroDollsImageSubTable.objects.get(id=id).delete()
    return JsonResponse({'success': True, 'message': 'Image deleted successfully'})

@login_required(login_url="login")
def view_shero_dolls(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    shero_dolls = SheroDollsImage.objects.get(id=id)
    shero_dolls_image = SheroDollsImageSubTable.objects.filter(shero_dolls_image_id=id)
    return render(request, "shero_dolls_management/view_shero_dolls.html", {"shero_dolls": shero_dolls, "shero_dolls_image": shero_dolls_image}) 




# GIFT CARD IMAGE CURD:
@login_required(login_url="login")
def view_giftcard_image(request):
    if is_normal_user(request):
        return redirect("web_login")
    image_data=GiftCardTypeImages.objects.distinct("giftcard_type_id")
    return render(request,'gift_card_image/view-giftcard-image.html',
        {
        'image_data':image_data,
        "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request),
     
        })
    


@login_required(login_url="login")
def add_giftcard_image(request):
    if is_normal_user(request):
        return redirect("web_login")
    giftcard_types = GiftCardType.objects.filter(is_active = True)
    giftcard_type_list = GiftCardTypeImages.objects.all().distinct('giftcard_type_id').values_list('giftcard_type_id', flat=True)
    try:
        if request.method=='POST':
            giftcard_type_id = request.POST.get("giftcard_type")
            images=request.FILES.getlist('images')
            for image in images:
                GiftCardTypeImages.objects.create(giftcard_type_id = giftcard_type_id, images = image)
            messages.success(request,'Gift card images Added')
            return redirect('view_giftcard_image')
    except:
        messages.error(request, "Add Successfully Not Done!!!")
        return redirect("add_giftcard_image")

    return render(request,'gift_card_image/add-gift-card-image.html',
        {"giftcard_types": giftcard_types,
        "giftcard_type_list": giftcard_type_list,
        "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request),
        })



@login_required(login_url="login")
def edit_giftcard_image(request,id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        giftcard_type = GiftCardType.objects.get(id=id, is_active = True)  
        giftcard_type_images = GiftCardTypeImages.objects.filter(giftcard_type_id = id)   
        # giftcard=GiftCardTypeImages.objects.distinct("giftcard_type_id")
        # giftcarddata = giftcard.get(giftcard_type_id = id)

        if request.method=='POST':
            giftcard_type=request.POST.get('giftcard_type')
            giftcard_image=request.FILES.getlist('giftcard_type_images')
            for image in giftcard_image:
                GiftCardTypeImages.objects.create(giftcard_type_id = id, images = image)
            messages.success(request, "Updated")
            return redirect("view_giftcard_image")

    except:
        messages.error(request, "Update Not Done")
        return redirect("edit_giftcard_image")

    return render(request,'gift_card_image/edit-gift-card-image.html',
        {'giftcard_type_images': giftcard_type_images,
        'giftcard_type': giftcard_type, 
        # 'giftcard_data':giftcarddata ,  
        "m": permission(request),
        "module_list": helper(request),
        "m_check": per(request) })

        
        

@login_required(login_url="login")
def delete_giftcard_image(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        id = request.POST.get("giftcard_image")
        GiftCardTypeImages.objects.filter(giftcard_type_id=id).delete()
    messages.success(request, "Deleted")
    return redirect("view_giftcard_image")


@csrf_exempt
def delete_giftcard_type_image(request):
    id = request.POST.get("giftcard_type_image")
    GiftCardTypeImages.objects.get(id = id).delete()
    return JsonResponse({'success': True, 'message': 'Image deleted successfully'})



# GIFT CARD CURD END 


# to delete shero dolls images apart from primary and og image
@csrf_exempt
def delete_shero_dolls_images(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("shero_dolls_image")
        SheroDollsImageSubTable.objects.get(id=id).delete()
        return JsonResponse({'success': True, 'message': 'Image deleted successfully'})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('shero_dolls')

# to show details of shero dolls
@login_required(login_url="login")
def view_shero_dolls(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        shero_dolls = SheroDollsImage.objects.get(id=id)
        shero_dolls_image = SheroDollsImageSubTable.objects.filter(shero_dolls_image_id=id)
        return render(request, "shero_dolls_management/view_shero_dolls.html", {"shero_dolls": shero_dolls, "shero_dolls_image": shero_dolls_image, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('shero_dolls') 
# Shero Dolls End



# Referral Start
@login_required(login_url="login")
def referral(request):
    if is_normal_user(request):
        return redirect("web_login")
    who_referred = UserReferral.objects.filter(is_delete = False).annotate(total_count=Count("user_from_id"))
    if who_referred.count() > 2:
        users_who_referred = UserReferral.objects.order_by("user_from_id").distinct("user_from_id").filter(is_delete = False)
    else:
        users_who_referred = None
    model = Module.objects.all().order_by("id")
    return render(request, "referral_management/referral.html", {"users_who_referred": users_who_referred, "m": permission(request),
            "model": model,
            "module_list": helper(request),
            "m_check": per(request)})

@login_required(login_url="login")
def view_referral_details(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    data = UserReferral.objects.filter(user_from_id = id)
    user_data = User.objects.get(id = id)
    given_dolls_count = user_data.dolls_got_count
    referral_count = data.count
    referral_order = data.filter(order_status = True)
    referral_order_count = referral_order.count()
    dolls_count = referral_order_count // 3
    model = Module.objects.all().order_by("id")
    dolls_to_receive = dolls_count-given_dolls_count
    no_of_dolls = range(1, dolls_to_receive + 1)

    try:
        user_address = UserAddress.objects.get(user_id = id, default_address = True)
    except:
        user_address = None

    if request.method == "POST":
        status = request.POST.get("status")
        dolls_sent_count = int(request.POST.get("dolls_sent_count"))
        user_data.referral_reward_status = status
        user_data.dolls_got_count += dolls_sent_count
        user_data.dolls_to_get_count = 0
        if user_data.dolls_to_get_count >= dolls_sent_count:
            user_data.dolls_to_get_count -= dolls_sent_count
        user_data.save()
        messages.success(request, "Reward Status Changed")
        return redirect('view_referral_details', id)
    return render(request, "referral_management/view_referral.html", 
    {"m": permission(request),
    "model": model,
    "module_list": helper(request),
    "m_check": per(request), 
    "dolls_to_receive": dolls_to_receive,
    "user_data": user_data,
    "given_dolls_count": given_dolls_count,
    "user_address": user_address,
    "no_of_dolls": no_of_dolls, 
    "referral_count": referral_count,
    "referral_order_count": referral_order_count,
    "dolls_count": dolls_count})
    
@login_required(login_url="login")
def delete_referral_user(request):
    if is_normal_user(request):
        return redirect("web_login")
    id = request.POST.get('delete_referral_user')
    referral_data = UserReferral.objects.filter(user_from_id = id, is_delete = False).order_by("id")
        
    i = 0
    for data in referral_data:
        data.is_delete = True
        data.save()
        i += 1 
        if i == 3:
            break  
    messages.success(request, "Record Deleted")
    return redirect('referral')
# Referral End

# Sloper Tool Management Start

# To view sloper template
@login_required(login_url="login")
def sloper_template(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        template_data = SloperTemplate.objects.all()
        return render(request, "sloper_tool_management/template/template.html", {'template_data': template_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("dashboard")

@login_required(login_url="login")# To add sloper template
def add_sloper_template(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            image = request.FILES.get("image")
            SloperTemplate.objects.create(name = name, status = status, image = image)
            messages.success(request, "Added")
            return redirect("sloper_template")
        template_data = SloperTemplate.objects.filter(status = True)
        return render(request, "sloper_tool_management/template/add.html", {'template_data': template_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_template")

@login_required(login_url="login")# To view details of sloper template
def view_sloper_template(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        template_data = SloperTemplate.objects.get(id = id)
        return render(request, "sloper_tool_management/template/view.html", {'template_data': template_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_template")

@login_required(login_url="login")# To edit sloper template
def edit_sloper_template(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        template_data = SloperTemplate.objects.get(id = id)
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            image = request.FILES.get("image")
            template_data.name = name
            template_data.status = status
            if image:
                template_data.image = image
            template_data.save()
            messages.success(request, "Edited")
            return redirect("sloper_template")
        return render(request, "sloper_tool_management/template/edit.html", {'template_data': template_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_template")

@login_required(login_url="login")# To delete sloper template
def delete_sloper_template(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("sloper_template")
        SloperTemplate.objects.get(id = id).delete()
        messages.success(request, "Deleted")
        return redirect(sloper_template)  
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_template")
@login_required(login_url="login")
def sloper_texture(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        texture_data = SloperTexture.objects.all()
        return render(request, "sloper_tool_management/texture/texture.html", {'texture_data': texture_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("dashboard")
@login_required(login_url="login")
def add_sloper_texture(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            image = request.FILES.get("image")
            SloperTexture.objects.create(name = name, status = status, image = image)
            messages.success(request, "Added")
            return redirect("sloper_texture")
        texture_data = SloperTexture.objects.filter(status = True)
        return render(request, "sloper_tool_management/texture/add.html", {'texture_data': texture_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_texture")
@login_required(login_url="login")
def view_sloper_texture(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        texture_data = SloperTexture.objects.get(id = id)
        return render(request, "sloper_tool_management/texture/view.html", {'texture_data': texture_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_texture")
@login_required(login_url="login")
def edit_sloper_texture(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        texture_data = SloperTexture.objects.get(id = id)
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            image = request.FILES.get("image")
            texture_data.name = name
            texture_data.status = status
            if image:
                texture_data.image = image
            texture_data.save()
            messages.success(request, "Edited")
            return redirect("sloper_texture")
        return render(request, "sloper_tool_management/texture/edit.html", {'texture_data': texture_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_texture")
@login_required(login_url="login")
def delete_sloper_texture(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("sloper_texture")
        SloperTexture.objects.get(id = id).delete()
        messages.success(request, "Deleted")
        return redirect("sloper_texture")
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_texture")
    
@login_required(login_url="login")
def sloper_element(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        element_data = SloperElement.objects.all()
        return render(request, "sloper_tool_management/element/element.html", {'element_data': element_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("dashboard")
@login_required(login_url="login")
def add_sloper_element(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            image = request.FILES.get("image")
            SloperElement.objects.create(name = name, status = status, image = image)
            messages.success(request, "Added")
            return redirect("sloper_element")
        element_data = SloperElement.objects.filter(status = True)
        return render(request, "sloper_tool_management/element/add.html", {'element_data': element_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_element")    
@login_required(login_url="login")
def view_sloper_element(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        element_data = SloperElement.objects.get(id = id)
        return render(request, "sloper_tool_management/element/view.html", {'element_data': element_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_element")
@login_required(login_url="login")
def edit_sloper_element(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        element_data = SloperElement.objects.get(id = id)
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            image = request.FILES.get("image")
            element_data.name = name
            element_data.status = status
            if image:
                element_data.image = image
            element_data.save()
            messages.success(request, "Edited")
            return redirect("sloper_element")
        return render(request, "sloper_tool_management/element/edit.html", {'element_data': element_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_element")
@login_required(login_url="login")
def delete_sloper_element(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("sloper_element")
        SloperElement.objects.get(id = id).delete()
        messages.success(request, "Deleted")
        return redirect("sloper_element")
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_element")


@login_required(login_url="login")
def sloper_multicolor_icon(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        multicolor_icon_data = SloperMulticolorIconSVG.objects.all().order_by('-id')
        return render(request, "sloper_tool_management/svg/svg.html", {'multicolor_icon_data': multicolor_icon_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("dashboard")
@login_required(login_url="login")
def add_sloper_multicolor_icon(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            svg_img = request.FILES.get("image")

            test = SloperMulticolorIconSVG(name = name, status = status, image = svg_img)
            test.save()
            messages.success(request, "Added Successfully")
            return redirect("sloper_multicolor_icon")
        return render(request, "sloper_tool_management/svg/add.html", {"m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_multicolor_icon")
@login_required(login_url="login")
def view_sloper_multicolor_icon(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        multicolor_icon_data = SloperMulticolorIconSVG.objects.get(id = id)
        return render(request, "sloper_tool_management/svg/view.html", {'multicolor_icon_data': multicolor_icon_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_multicolor_icon")
@login_required(login_url="login")
def edit_sloper_multicolor_icon(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        multicolor_icon_data = SloperMulticolorIconSVG.objects.get(id = id)
        if request.method == "POST":
            name = request.POST.get("name")
            status = request.POST.get("status")
            image = request.FILES.get("image")
            multicolor_icon_data.name = name
            multicolor_icon_data.status = status
            if image:
                multicolor_icon_data.image = image
            multicolor_icon_data.save()
            messages.success(request, "Edited")
            return redirect("sloper_multicolor_icon")
        return render(request, "sloper_tool_management/svg/edit.html", {'multicolor_icon_data': multicolor_icon_data, "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)})
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_multicolor_icon")
@login_required(login_url="login")
def delete_sloper_multicolor_icon(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("sloper_svg")
        SloperMulticolorIconSVG.objects.get(id = id).delete()
        messages.success(request, "Deleted")
        return redirect("sloper_multicolor_icon")
    except:
        messages.success(request, "Something Went Wrong ")
        return redirect("sloper_multicolor_icon")

# Sloper Tool Management End

@login_required(login_url="login")# Notification Start
def inquiry_notification(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        notifications = Notification.objects.filter(notification_type = 'INQUIRY').order_by("-id")
        return render(request, "notification_management/inquiry.html", {"notifications": notifications, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('dashboard')

@login_required(login_url="login")
def delete_inquiry_notification(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        Notification.objects.get(id = id).delete()
        messages.success(request, "Deleted")
        return redirect(inquiry_notification)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('inquiry_notification')

@login_required(login_url="login")
def referral_notification(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        notifications = Notification.objects.filter(notification_type = 'REFERRER').order_by("-id")
        return render(request, "notification_management/referral.html", {"notifications": notifications, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})
    except:
        messages.error("Something Went Wrong")
        return redirect('dashboard')        
@login_required(login_url="login")
def delete_referral_notification(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        Notification.objects.get(id = id).delete()
        messages.success(request, "Deleted")
        return redirect(referral_notification)
    except:
        messages.error("Something Went Wrong")
        return redirect('referral_notification')
@login_required(login_url="login")
def notification(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:    
        total_notification = Notification.objects.all().count()
        total_inquiry_notification = Notification.objects.filter(notification_type = "INQUIRY").count()
        total_referral_notification = Notification.objects.filter(notification_type = "REFERRER").count()
        return JsonResponse({"total_notification": total_notification, "total_inquiry_notification": total_inquiry_notification, "total_referral_notification": total_referral_notification})
    except:
        messages.error("Something Went Wrong")
        return redirect('dashboard')
@login_required(login_url="login")
def view_inquiry_notification(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        Notification.objects.get(id = id).delete()
        return redirect("contact_us_inquiry")
    except:
        messages.error("Something Went Wrong")
        return redirect('inquiry_notification')
@login_required(login_url="login")
def view_referral_notification(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        Notification.objects.get(id = id).delete()
        return redirect("referral")    
    except:
        messages.error("Something Went Wrong")
        return redirect('referral_notification')
@login_required(login_url="login")
def delete_all_inquiry_notification(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        Notification.objects.filter(notification_type = 'INQUIRY').delete()
        messages.success(request, "Deleted")
        return redirect('inquiry_notification')
    except:
        messages.error("Something Went Wrong")
        return redirect('inquiry_notification')
@login_required(login_url="login")
def delete_all_referral_notification(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        Notification.objects.filter(notification_type = 'REFERRER').delete()
        messages.success(request, "Deleted")
        return redirect('inquiry_notification')
    except:
        messages.error("Something Went Wrong")
        return redirect('referral_notification')
# Notification End    

@login_required(login_url="login")# About us start
def about_us_management(request):
    if is_normal_user(request):
        return redirect("web_login")
    about_us_data = AboutUs.objects.get(id = 1)
    if request.method == "POST":
        heading_1 = request.POST.get("heading_1")
        image_1 = request.FILES.get("image_1")
        content_1 = request.POST.get("editor_1")
        if image_1:
            about_us_data.image_1 = image_1
        about_us_data.heading_1 = heading_1
        about_us_data.content_1 = content_1

        heading_2 = request.POST.get("heading_2")
        image_2 = request.FILES.get("image_2")
        content_2 = request.POST.get("editor_2")
        if image_2:
            about_us_data.image_2 = image_2
        about_us_data.heading_2 = heading_2
        about_us_data.content_2 = content_2

        heading_3 = request.POST.get("heading_3")
        content_3 = request.POST.get("editor_3")
        about_us_data.heading_3 = heading_3
        about_us_data.content_3 = content_3

        heading_4 = request.POST.get("heading_4")
        image_4 = request.FILES.get("image_4")
        content_4 = request.POST.get("editor_4")

        if image_4:
            about_us_data.image_4 = image_4
        about_us_data.heading_4 = heading_4
        about_us_data.content_4 = content_4

        heading_5 = request.POST.get("heading_5")
        content_5 = request.POST.get("editor_5")
        about_us_data.heading_5 = heading_5
        about_us_data.content_5 = content_5

        about_us_data.save()
        messages.success(request,"Edited")
        return render(request, "about_us_management/about_us.html", {'about_us_data': about_us_data, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})
    return render(request, "about_us_management/about_us.html", {'about_us_data': about_us_data, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})
@login_required(login_url="login")# About us End
def shero_subscription_content(request):
    if is_normal_user(request):
        return redirect("web_login")
    shero_subscription_data = SheroSubscriptionContent.objects.get(id=1)
    if request.method == "POST":
        banner_image = request.FILES.get("banner_image")
        if banner_image:
            shero_subscription_data.banner_image = banner_image
        banner_image_content = request.POST.get("banner_image_content")
        intro_paragraph = request.POST.get("intro_paragraph")
        shero_benefits_title = request.POST.get("shero_benefits_title")
        shero_benefits_image_1 = request.FILES.get("shero_benefits_image_1")
        if shero_benefits_image_1:
            shero_subscription_data.shero_benefits_image_1 = shero_benefits_image_1
        shero_benefits_content_1 = request.POST.get("shero_benefits_content_1")
        shero_benefits_image_2 = request.FILES.get("shero_benefits_image_2")
        if shero_benefits_image_2:
            shero_subscription_data.shero_benefits_image_2 = shero_benefits_image_2
        shero_benefits_content_2 = request.POST.get("shero_benefits_content_2")
        shero_benefits_image_3 = request.FILES.get("shero_benefits_image_3")
        if shero_benefits_image_3:
            shero_subscription_data.shero_benefits_image_3 = shero_benefits_image_3
        shero_benefits_content_3 = request.POST.get("shero_benefits_content_3")
        shero_benefits_image_4 = request.FILES.get("shero_benefits_image_4")
        if shero_benefits_image_4:
            shero_subscription_data.shero_benefits_image_4 = shero_benefits_image_4
        shero_benefits_content_4 = request.POST.get("shero_benefits_content_4")
        shero_benefits_image_5 = request.FILES.get("shero_benefits_image_5")
        if shero_benefits_image_5:
            shero_subscription_data.shero_benefits_image_5 = shero_benefits_image_5
        shero_benefits_content_5 = request.POST.get("shero_benefits_content_5")
        shero_how_it_works_title = request.POST.get("shero_how_it_works_title")
        shero_how_it_works_title_1 = request.POST.get("shero_how_it_works_title_1")
        shero_how_it_works_content_1 = request.POST.get("shero_how_it_works_content_1")
        shero_how_it_works_image_1 = request.FILES.get("shero_how_it_works_image_1")
        if shero_how_it_works_image_1:
            shero_subscription_data.shero_how_it_works_image_1 = shero_how_it_works_image_1
        shero_how_it_works_title_2 = request.POST.get("shero_how_it_works_title_2")
        shero_how_it_works_content_2 = request.POST.get("shero_how_it_works_content_2")
        shero_how_it_works_image_2 = request.FILES.get("shero_how_it_works_image_2")
        if shero_how_it_works_image_2:
            shero_subscription_data.shero_how_it_works_image_2 = shero_how_it_works_image_2
        shero_how_it_works_title_3 = request.POST.get("shero_how_it_works_title_3")
        shero_how_it_works_content_3 = request.POST.get("shero_how_it_works_content_3")
        shero_how_it_works_image_3 = request.FILES.get("shero_how_it_works_image_3")
        if shero_how_it_works_image_3:
            shero_subscription_data.shero_how_it_works_image_3 = shero_how_it_works_image_3
        shero_how_it_works_title_4 = request.POST.get("shero_how_it_works_title_4")
        shero_how_it_works_content_4 = request.POST.get("shero_how_it_works_content_4")
        shero_how_it_works_image_4 = request.FILES.get("shero_how_it_works_image_4")
        if shero_how_it_works_image_4:
            shero_subscription_data.shero_how_it_works_image_4 = shero_how_it_works_image_4
        create_play_image = request.FILES.get("create_play_image")
        if create_play_image:
            shero_subscription_data.create_play_image = create_play_image
        invite_your_friend_image = request.FILES.get("invite_your_friend_image")
        if invite_your_friend_image:
            shero_subscription_data.invite_your_friend_image = invite_your_friend_image
          

        shero_subscription_data.intro_paragraph = intro_paragraph
        shero_subscription_data.shero_benefits_title = shero_benefits_title
        shero_subscription_data.shero_benefits_content_1 = shero_benefits_content_1
        shero_subscription_data.shero_benefits_content_2 = shero_benefits_content_2   
        shero_subscription_data.shero_benefits_content_3 = shero_benefits_content_3
        shero_subscription_data.shero_benefits_content_4 = shero_benefits_content_4
        shero_subscription_data.shero_benefits_content_5 = shero_benefits_content_5
        shero_subscription_data.shero_how_it_works_title = shero_how_it_works_title
        shero_subscription_data.shero_how_it_works_content_1 = shero_how_it_works_content_1
        shero_subscription_data.shero_how_it_works_content_2 = shero_how_it_works_content_2
        shero_subscription_data.shero_how_it_works_content_3 = shero_how_it_works_content_3
        shero_subscription_data.shero_how_it_works_content_4 = shero_how_it_works_content_4
        shero_subscription_data.shero_how_it_works_title_1 = shero_how_it_works_title_1
        shero_subscription_data.shero_how_it_works_title_2 = shero_how_it_works_title_2
        shero_subscription_data.shero_how_it_works_title_3 = shero_how_it_works_title_3
        shero_subscription_data.shero_how_it_works_title_4 = shero_how_it_works_title_4
        shero_subscription_data.banner_image_content = banner_image_content
        shero_subscription_data.save()
        messages.success(request,"Edited")
        return render(request, "shero_subscription_content/shero_subscription_content.html", {'shero_subscription_data': shero_subscription_data, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})
    return render(request, "shero_subscription_content/shero_subscription_content.html", {'shero_subscription_data': shero_subscription_data, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})

@login_required(login_url="login")
def blog_content(request):
    if is_normal_user(request):
        return redirect("web_login")
    blog_content_data = BlogContent.objects.get(id = 1)
    if request.method == "POST":
        heading = request.POST.get("heading")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        blog_content_data.heading = heading
        blog_content_data.description = description
        if image:
            blog_content_data.image = image
        blog_content_data.save()
        messages.success(request, "Edited")
        return redirect("blog_content")
    return render(request, "blog_management/blog_content/blog_content.html", {"blog_content": blog_content_data, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})

@login_required(login_url="login")
def contact_us_content(request):
    if is_normal_user(request):
        return redirect("web_login")
    contect_us_data = ContectUsContent.objects.get(id = 1)
    if request.method == "POST":
        heading = request.POST.get("heading")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        contect_us_data.heading = heading
        contect_us_data.description = description
        if image:
            contect_us_data.image = image
        contect_us_data.save()
        messages.success(request, "Edited")
        return redirect("contact_us_content")
    return render(request, "contact_us_content/contact_us_content.html", {"contact_us": contect_us_data, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})    
@login_required(login_url="login")
def referral_content(request):
    if is_normal_user(request):
        return redirect("web_login")
    referral_data = ReferralContent.objects.get(id = 1)
    if request.method == "POST":
        image = request.FILES.get("image")
        content = request.POST.get("content")
        referral_data.content = content
        if image:
            referral_data.image = image
        referral_data.save()
        messages.success(request, "Edited")
        return redirect("referral_content")
    return render(request, "referral_content_management/referral_content.html", {"referral_data": referral_data, "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)})
@login_required(login_url="login")    
def edit_token_and_key(request, token_and_key_id):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        token_and_key = TokenAndSecretKey.objects.get(id=token_and_key_id)
        if request.method == "POST":
            name = request.POST.get('name')
            value = request.POST.get('value')
            
            token_and_key.name = name
            token_and_key.value = value
            token_and_key.save()
            
            messages.success(request, "Update Successfully")
            return redirect('view_token_and_key')
        return render(request, "token_and_key_management/edit.html", {'token_and_key': token_and_key, "m": permission(request), 
                "module_list": helper(request),
                "m_check": per(request)})
    except:
        messages.success(request, "Failed to Edit")
        return redirect('view_token_and_key')
@login_required(login_url="login")    
def view_token_and_key(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        tokens_and_keys = TokenAndSecretKey.objects.all()
        return render(request, "token_and_key_management/view.html", {'tokens_and_keys': tokens_and_keys, "m": permission(request),
                    "module_list": helper(request),
                    "m_check": per(request)})
    except:
        return render(request, "token_and_key_management/view.html", {'tokens_and_keys': None, "m": permission(request),
                    "module_list": helper(request),
                    "m_check": per(request)})

@login_required(login_url="login")
def view_guest_user_order(request):
    if is_normal_user(request):
        return redirect("web_login")
    guest_user_data = GuestUserData.objects.all().order_by('-id')
    for i in guest_user_data:
        i.total_amount += i.tax + i.shipping_charge
    return render(request, "order_management/guest-user-order/view.html", 
        {
            "orders": guest_user_data, 
            "m": permission(request),
            "module_list": helper(request),
            "m_check": per(request)
        }
    )
@login_required(login_url="login")
def view_guest_user_order_detail(request, id):
    if is_normal_user(request):
        return redirect("web_login")
    guest_user_data = GuestUserData.objects.filter(id=id)
    if guest_user_data:
        guest_user_data = guest_user_data.first()
        return render(request, "order_management/guest-user-order/view-detail.html", 
            {
                'order': guest_user_data,
                "m": permission(request),
                "module_list": helper(request),
                "m_check": per(request)
            }
        )
    else:
        messages.error(request, "Record Not Found")
        return redirect('view_guest_user_order')
@login_required(login_url="login")
def delete_guest_user_order(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        id = request.POST.get("order_id")
        GuestUserData.objects.filter(id=id).delete()
        messages.success(request, "Deleted Successfully")
        return redirect('view_guest_user_order')
    except:
        messages.success(request, "Failed to Delete")
        return redirect('view_guest_user_order')

@login_required(login_url="login")
def edit_banner_img(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        banner_images = SloperLandingPageBannerImage.objects.all().order_by('id')
        if request.method == 'POST':
            img_1 = request.FILES.get('banner_img_1')
            video = request.FILES.get('banner_video')
            img_2 = request.FILES.get('banner_img_2')

            if img_1:
                try:
                    banner_obj_1 = banner_images[0]
                except:
                    banner_obj_1 = SloperLandingPageBannerImage()
                banner_obj_1.banner_img  = img_1
                banner_obj_1.save()
            if video:
                try:
                    video_obj = banner_images[1]
                except:
                    video_obj = SloperLandingPageBannerImage()
                video_obj.banner_img = video
                video_obj.save()
            if img_2:
                try:
                    banner_obj_2 = banner_images[2]
                except:
                    banner_obj_2 = SloperLandingPageBannerImage()
                banner_obj_2.banner_img = img_2
                banner_obj_2.save()

            messages.success(request, "Updated Successfully")
            return redirect('edit_banner_img')
        return render(request, 'sloper-landing-page-management/banner-images/edit.html', {'banner_images': banner_images, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
    except:
        messages.error(request, "Failed to Update")
        return redirect('dashboard')
@login_required(login_url="login")
def edit_how_it_work(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        how_it_work = SloperLandingPageHowItWork.objects.get()
    except:
        how_it_work = SloperLandingPageHowItWork()
    try:
        if request.method == "POST":
            title = request.POST.get('title')
            description = request.POST.get('description')
            how_it_work.title = title
            how_it_work.description = description
            how_it_work.save()
            messages.success(request, 'Updated Successfully')
            return redirect('edit_how_it_work')
        return render(request, 'sloper-landing-page-management/how-it-works/edit.html', {'how_it_work': how_it_work, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
    except:
        messages.error(request, 'Failed To Update')
        return redirect('dashboard')
@login_required(login_url="login")
def add_how_it_work_section(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            img = request.FILES.get('img')
            description = request.POST.get('description')
            SloperLandingPageHowItWorkSection.objects.create(img=img, description=description)
            messages.success(request, "Created Successfully")
            return redirect('view_how_it_work_section')
        return render(request, 'sloper-landing-page-management/how-it-works/how-it-work-section/add.html', {"m": permission(request), "module_list": helper(request), "m_check": per(request)})
    except:
        messages.success(request, "Failed to Create")
        return redirect('view_how_it_work_section')
@login_required(login_url="login")
def view_how_it_work_section(request):
    if is_normal_user(request):
        return redirect("web_login")
    how_it_work_sections = SloperLandingPageHowItWorkSection.objects.all()
    return render(request, 'sloper-landing-page-management/how-it-works/how-it-work-section/view.html', {'how_it_work_sections': how_it_work_sections, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
@login_required(login_url="login")
def edit_how_it_work_section(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        how_it_work_section = SloperLandingPageHowItWorkSection.objects.get(slug=slug)
        if request.method == "POST":
            img = request.FILES.get('img')
            description = request.POST.get('description')
            how_it_work_section.img = img
            how_it_work_section.description = description
            how_it_work_section.save()
            messages.success(request, 'Updated Successfully')
            return redirect('view_how_it_work_section')
        return render(request, 'sloper-landing-page-management/how-it-works/how-it-work-section/edit.html', {'how_it_work_section': how_it_work_section, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
    except:
        messages.error(request, 'Failed to Update')
        return redirect('view_how_it_work_section')
@login_required(login_url="login")
def delete_how_it_work_section(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        slug = request.POST.get('slug')
        SloperLandingPageHowItWorkSection.objects.filter(slug=slug).delete()
        messages.success(request, 'Deleted Successfully')
        return redirect('view_how_it_work_section')
    except:
        messages.error(request, 'Failed to Delete')
        return redirect('view_how_it_work_section')
@login_required(login_url="login")
def edit_testimonial(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        testimonial = SloperLandingPageTestimonial.objects.get()
    except:
        testimonial = SloperLandingPageTestimonial()
    try:
        if request.method == "POST":
            title = request.POST.get('title')
            description = request.POST.get('description')
            rating = request.POST.get('rating')
            review_count = request.POST.get('review_count')

            testimonial.title = title
            testimonial.description = description
            testimonial.rating = rating
            testimonial.review_count = review_count
            testimonial.save()
            messages.success(request, 'Updated Successfully')
            return redirect('edit_testimonial')
        return render(request, 'sloper-landing-page-management/testimonials/edit.html', {'testimonial': testimonial, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
    except:
        messages.error(request, 'Failed to Update')
        return redirect('edit_testimonial')
@login_required(login_url="login")
def view_testimonial_section(request):
    if is_normal_user(request):
        return redirect("web_login")
    testimonial_sections = SloperLandingPageTestimonialSection.objects.all()
    return render(request, 'sloper-landing-page-management/testimonials/testimonial-section/view.html', {'testimonial_sections': testimonial_sections, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
@login_required(login_url="login")
def add_testimonial_section(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == 'POST':
        img = request.FILES.get('img')
        rating = request.POST.get('rating')
        description = request.POST.get('description')
        SloperLandingPageTestimonialSection.objects.create(img=img, rating=rating, description=description)
        messages.success(request, 'Added Successfully')
        return redirect('view_testimonial_section')
    return render(request, 'sloper-landing-page-management/testimonials/testimonial-section/add.html', {"m": permission(request), "module_list": helper(request), "m_check": per(request)})
@login_required(login_url="login")
def edit_testimonial_section(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        testimonial_section = SloperLandingPageTestimonialSection.objects.get(slug=slug)
        if request.method == 'POST':
            img = request.FILES.get('img')
            rating = request.POST.get('rating')
            description = request.POST.get('description')
            if img:
                testimonial_section.img = img

            testimonial_section.rating = rating
            testimonial_section.description = description
            testimonial_section.save()
            messages.success(request, 'Updated Successfully')
            return redirect('view_testimonial_section')
        return render(request, 'sloper-landing-page-management/testimonials/testimonial-section/edit.html', {"testimonial_section": testimonial_section, "m": permission(request), "module_list": helper(request), "m_check": per(request)})
    except:
        messages.error(request, 'Failed to Update')
        return redirect('view_testimonial_section')
@login_required(login_url="login")
def delete_testimonial_section(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            slug = request.POST.get('slug')
            SloperLandingPageTestimonialSection.objects.get(slug=slug).delete()
            messages.success(request, 'Delete Successfully')
        return redirect('view_testimonial_section')
    except:
        messages.error(request, 'Failed To Delete')
        return redirect('view_testimonial_section')
@login_required(login_url="login")
def sloper_subscription_management(request):
    return render(request, "sloper-subscription-management/create-plan.html")
@login_required(login_url="login")
def sloper_plan_category(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        category_data = SloperPlanCategory.objects.all()
        return render(request, "sloper_subscription_plan_management/plan_category.html", 
                                {"category_data":category_data,
                                "m": permission(request),
                                "module_list": helper(request),
                                "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('dashboard')                        

@login_required(login_url="login")
def add_sloper_plan_category(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            category = request.POST.get('plan_category')
            status = request.POST.get('status')
            SloperPlanCategory.objects.create(name = category, is_active = status)
            messages.success(request, "Category Created")
            return redirect('sloper_plan_category')
        return render(request, "sloper_subscription_plan_management/add_plan_category.html", 
                                {"m": permission(request),
                                "module_list": helper(request),
                                "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('sloper_plan_category')

@login_required(login_url="login")
def edit_sloper_plan_category(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        category_data = SloperPlanCategory.objects.get(slug=slug)
        category_title = category_data.category_title
        price = SloperBasicPrice.objects.filter(category_id = category_data.id)
        if request.method == "POST":
            category = request.POST.get('plan_category')
            status = request.POST.get('status')
            category_data.name = category
            category_data.is_active = status
            category_data.save()
            if category_title == "Individual Plan":
                price_per_month = request.POST.get('price_per_month')
                individual_price = SloperBasicPrice.objects.get_or_create(category_id = category_data.id)
                individual_price[0].price = price_per_month
                individual_price[0].name = "Price Per Month" 
                individual_price[0].save()
            if category_title == "Hospital":
                price_per_patient = request.POST.get('price_per_patient')
                hospital_price = SloperBasicPrice.objects.get_or_create(category_id = category_data.id)
                hospital_price[0].price = price_per_patient
                hospital_price[0].name = "Price Per Patient"
                hospital_price[0].save()
            if category_title == "School":
                price_per_student = request.POST.get('price_per_student')
                price_per_class = request.POST.get('price_per_class')
                discount_on_school_plan = request.POST.get('discount_on_school_plan')
                SloperBasicPrice.objects.filter(category_id = category_data.id).delete()
                SloperBasicPrice.objects.create(category_id = category_data.id, name = "Price Per Student", price = price_per_student)
                SloperBasicPrice.objects.create(category_id = category_data.id, name = "Price Per Teacher", price = price_per_class)
                SloperBasicPrice.objects.create(category_id = category_data.id, name = "Discount on School Plan", price = discount_on_school_plan)

            messages.success(request, "Edited")
            return redirect("sloper_plan_category")
        return render(request, "sloper_subscription_plan_management/edit_plan_category.html", 
                                {"prices": price,
                                "category_title":category_title,
                                "category_data":category_data,
                                "m": permission(request),
                                "module_list": helper(request),
                                "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('sloper_plan_category')                            

@login_required(login_url="login")
def sloper_plans(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        sloper_plan_data = SloperPlan.objects.all()
        return render(request, "sloper_subscription_plan_management/sloper_plans.html", {"sloper_plan_data": sloper_plan_data, "m": permission(request),
                            "module_list": helper(request),
                            "m_check": per(request)}) 
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('dashboard')                              

@login_required(login_url="login")
def add_sloper_plan(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        category_data = SloperPlanCategory.objects.all()
        if request.method == "POST":
            category = request.POST.get("category")
            status = request.POST.get("status")
            plan_name = request.POST.get("plan_name")
            plan_percentage_discount = request.POST.get("discount")
            from_user_count = request.POST.get("from_user")
            upto_user_count = request.POST.get("upto_user")
            data = {"type": plan_name, "off": plan_percentage_discount}
            SloperPlan.objects.create(category_id = category, name = plan_name, from_user = from_user_count, upto_user = upto_user_count, is_active = status, data = data)
            messages.success(request, "Plan Created")
            return redirect("sloper_plans")
        return render(request, "sloper_subscription_plan_management/add_sloper_plan.html", 
                            {  "categories": category_data,
                               "m": permission(request),
                               "module_list": helper(request),
                               "m_check": per(request)  })
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('sloper_plans')  

@login_required(login_url="login")
def edit_sloper_plan(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        plan_data = SloperPlan.objects.get(slug = slug)
        if request.method == "POST":
            status = request.POST.get("status")
            plan_name = request.POST.get("plan_name")
            from_user = request.POST.get("from_user")
            upto_user = request.POST.get("upto_user")
            plan_benefit = request.POST.get("discount")  
            plan_data.is_active = status
            plan_data.name = plan_name
            plan_data.from_user = from_user
            plan_data.upto_user = upto_user
            data = {"type": plan_name, "off": plan_benefit}
            plan_data.data = data
            plan_data.save()
            messages.success(request, "Plan Edited")
            return redirect('sloper_plans')
        return render(request, "sloper_subscription_plan_management/edit_sloper_plan.html", 
                            { "plan_data": plan_data, 
                               "m": permission(request),
                               "module_list": helper(request),
                               "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('sloper_plans')                        

@login_required(login_url="login")
def delete_sloper_plan(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        plan_id = request.POST.get("plan_id")
        SloperPlan.objects.get(id = plan_id).delete()
        messages.success(request, "Deleted")
        return redirect('sloper_plans')   
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('sloper_plans')   

@login_required(login_url="login")
def sloper_hospitals(request):
    if is_normal_user(request):
        return redirect("web_login")
    hospitals = SloperHospital.objects.all()
    return render(request, 'sloper_subscription_plan_management/sloper-hospitals/sloper_hospitals.html', {"hospitals":hospitals, "m": permission(request),
                               "module_list": helper(request),
                               "m_check": per(request)})  

@login_required(login_url="login")
def add_sloper_hospital(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        name = request.POST["name"]
        management_name = request.POST["management_name"]
        management_email = request.POST["management_email"]
        city = request.POST["city"]
        state = request.POST["state"]
        country = request.POST["country"]
        zipcode = request.POST["zipcode"]
        phone_number = request.POST["phone_number"]
        is_active = request.POST["is_active"]
        SloperHospital.objects.create(name=name, management_name=management_name, management_email=management_email, city=city, state=state,
         country=country, zipcode=zipcode, phone_number=phone_number, is_active=is_active)
        if not User.objects.filter(email = management_email).exists():
            password = random.randint(100000, 999999)
            user = User.objects.create(email = management_email, name = name, is_verified = True, is_mail_send = True, user_type="CUSTOMER", password = password)
            UserRole.objects.create(user_id = user.id, role = "HOSPITAL")
            mail_to_hospital_on_add(name, management_email, password)
        else:
            user = User.objects.get(email = management_email)
            UserRole.objects.create(user_id = user.id, role = "HOSPITAL")
            mail_to_hospital_on_add(name, management_email)
        messages.success(request, "Hospital Added")
        return redirect("sloper_hospitals")
    return render(request, 'sloper_subscription_plan_management/sloper-hospitals/add.html', {"m": permission(request),
                               "module_list": helper(request),
                               "m_check": per(request)})


@login_required(login_url="login")
def edit_sloper_hospital(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    hospital = SloperHospital.objects.get(slug = slug)
    if request.method == "POST":
        name = request.POST["name"]
        management_name = request.POST["management_name"]
        management_email = request.POST["management_email"]
        city = request.POST["city"]
        state = request.POST["state"]
        country = request.POST["country"]
        zipcode = request.POST["zipcode"]
        phone_number = request.POST["phone_number"]
        is_active = request.POST["is_active"]
        hospital.name = name
        hospital.management_name = management_name
        hospital.management_email = management_email
        hospital.city = city
        hospital.state = state
        hospital.country = country
        hospital.zipcode = zipcode
        hospital.phone_number = phone_number
        hospital.is_active = is_active
        hospital.save()
        messages.success(request, "Hospital Edited")
        return redirect("sloper_hospitals")
    return render(request, 'sloper_subscription_plan_management/sloper-hospitals/edit.html',
                                                            {"hospital": hospital, "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})

@login_required(login_url="login")
def delete_sloper_hospital(request):
    if is_normal_user(request):
        return redirect("web_login")
    slug = request.POST["delete_sloper_hospital"]
    SloperHospital.objects.get(slug = slug).delete()
    messages.success(request, "Deleted")
    return redirect("sloper_hospitals")



# Sloper School Start
@login_required(login_url="login")
def sloper_schools(request):
    if is_normal_user(request):
        return redirect("web_login")
    schools = SloperSchool.objects.all()
    return render(request, 'sloper_subscription_plan_management/sloper-schools/sloper_schools.html', {"schools":schools, "m": permission(request),
                               "module_list": helper(request),
                               "m_check": per(request)})  

@login_required(login_url="login")
def add_sloper_school(request):
    if is_normal_user(request):
        return redirect("web_login")
    if request.method == "POST":
        name = request.POST["name"]
        management_name = request.POST["management_name"]
        management_email = request.POST["management_email"]
        city = request.POST["city"]
        state = request.POST["state"]
        country = request.POST["country"]
        zipcode = request.POST["zipcode"]
        phone_number = request.POST["phone_number"]
        is_active = request.POST["is_active"]
        SloperSchool.objects.create(name=name, management_name=management_name, management_email=management_email, city=city, state=state,
         country=country, zipcode=zipcode, phone_number=phone_number, is_active=is_active)
        if not User.objects.filter(email = management_email).exists():
            password = random.randint(100000, 999999)
            user = User.objects.create(email = management_email, name = name, is_verified = True, is_mail_send = True, user_type="CUSTOMER", password = password)
            UserRole.objects.create(user_id = user.id, role = "School")
            mail_to_school_on_add(name, management_email, password)
        else:
            user = User.objects.get(email = management_email)
            UserRole.objects.create(user_id = user.id, role = "School")
            mail_to_school_on_add(name, management_email)
        messages.success(request, "School Added")
        return redirect("sloper_schools")
    return render(request, 'sloper_subscription_plan_management/sloper-schools/add.html', {"m": permission(request),
                               "module_list": helper(request),
                               "m_check": per(request)})


@login_required(login_url="login")
def edit_sloper_school(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    school = SloperSchool.objects.get(slug = slug)
    if request.method == "POST":
        name = request.POST["name"]
        management_name = request.POST["management_name"]
        management_email = request.POST["management_email"]
        city = request.POST["city"]
        state = request.POST["state"]
        country = request.POST["country"]
        zipcode = request.POST["zipcode"]
        phone_number = request.POST["phone_number"]
        is_active = request.POST["is_active"]
        school.name = name
        school.management_name = management_name
        school.management_email = management_email
        school.city = city
        school.state = state
        school.country = country
        school.zipcode = zipcode
        school.phone_number = phone_number
        school.is_active = is_active
        school.save()
        messages.success(request, "School Edited")
        return redirect("sloper_schools")
    return render(request, 'sloper_subscription_plan_management/sloper-schools/edit.html',
                                                            {"school": school, "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})

@login_required(login_url="login")
def delete_sloper_school(request):
    if is_normal_user(request):
        return redirect("web_login")
    slug = request.POST["delete_sloper_school"]
    SloperSchool.objects.get(slug = slug).delete()
    messages.success(request, "Deleted")
    return redirect("sloper_schools")
# Sloper School End

@login_required(login_url="login")
def individual_personal_sloper_subscriber(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        individual_personal_subscription = UserSloperSubscription.objects.filter(is_gifted = False, category = "Individual")
        return render(request, "sloper_subscriber_management/individual_personal/subscriber.html",
                                                            {"individual_personal_subscription":individual_personal_subscription,
                                                             "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")                                                           

@login_required(login_url="login")
def view_individual_personal_sloper_subscriber(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        individual_personal_subscription = UserSloperSubscription.objects.get(slug=slug)
        return render(request, "sloper_subscriber_management/individual_personal/view.html", 
                                                            {"individual_personal_subscription":individual_personal_subscription, 
                                                             "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})  
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("individual_personal_sloper_subscriber")

@login_required(login_url="login")
def individual_gift_sloper_subscriber(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        individual_gifted_subscription = UserGiftSloperPlan.objects.filter(user_sloper_subscription__is_gifted=True, user_sloper_subscription__category = "Individual")
        return render(request, "sloper_subscriber_management/individual_gift/subscriber.html", 
                                                            {"individual_gifted_subscription": individual_gifted_subscription,
                                                             "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})  
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")

@login_required(login_url="login")
def view_individual_gift_sloper_subscriber(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        individual_gifted_subscription = UserGiftSloperPlan.objects.get(slug=slug)
        return render(request, "sloper_subscriber_management/individual_gift/view.html",
                                                            {"individual_gifted_subscription": individual_gifted_subscription, 
                                                             "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})      
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("individual_gift_sloper_subscriber")

@login_required(login_url="login")
def hospital_sloper_subscriber(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        hospital_subscription = UserGiftSloperPlan.objects.filter(user_sloper_subscription__category = "Hospital")
        return render(request, "sloper_subscriber_management/hospital/subscriber.html", 
                                                            {"hospital_subscription": hospital_subscription, 
                                                             "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})  
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")

@login_required(login_url="login")
def view_hospital_sloper_subscriber(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        hospital_subscription = UserGiftSloperPlan.objects.get(slug=slug)
        return render(request, "sloper_subscriber_management/hospital/view.html",
                                                            {"hospital_subscription":hospital_subscription,
                                                            "m": permission(request),
                                                            "module_list": helper(request),
                                                            "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("hospital_sloper_subscriber")                                                           

@login_required(login_url="login")
def shipping_prices(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        shipping_prices = ShippingPrice.objects.all()
        return render(request, "shipping-prices/shipping_prices.html", {"shipping_prices":shipping_prices,
                                                                        "m": permission(request),
                                                                        "module_list": helper(request),
                                                                        "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")

@login_required(login_url="login")
def add_shipping_price(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        if request.method == "POST":
            order_value_from = request.POST.get('order_value_from') if request.POST.get('order_value_from') else 0
            order_value_upto = request.POST.get('order_value_upto') if request.POST.get('order_value_upto') else 0
            shipping_cost = request.POST.get('shipping_cost') if request.POST.get('shipping_cost') else 0
            ShippingPrice.objects.create(order_value_from=order_value_from,order_value_upto=order_value_upto,shipping_cost=shipping_cost)
            messages.success(request, "Successfully Added")
            return redirect("shipping_prices")
        return render(request, "shipping-prices/add.html", {"m": permission(request),
                                                            "module_list": helper(request),
                                                            "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("dashboard")

@login_required(login_url="login")
def edit_shipping_price(request, slug):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        shipping_price = ShippingPrice.objects.get(slug=slug)
        if request.method == "POST":
            shipping_price.order_value_from = request.POST.get('order_value_from') if request.POST.get('order_value_from') else 0
            shipping_price.order_value_upto = request.POST.get('order_value_upto') if request.POST.get('order_value_upto') else 0
            shipping_price.shipping_cost = request.POST.get('shipping_cost') if request.POST.get('shipping_cost') else 0
            shipping_price.save()
            messages.success(request, "Successfully Edited")
            return redirect("shipping_prices")
        return render(request, "shipping-prices/edit.html", {"shipping_price":shipping_price, 
                                                             "m": permission(request),
                                                             "module_list": helper(request),
                                                             "m_check": per(request)})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("shipping_prices")
@login_required(login_url="login")
def delete_shipping_price(request):
    if is_normal_user(request):
        return redirect("web_login")
    try:
        ShippingPrice.objects.get(slug=request.POST['shipping_price_slug']).delete()
        messages.success(request, "Deleted")
        return redirect("shipping_prices")
    except:
        messages.error(request, "Something Went Wrong")
        return redirect("shipping_prices")
@login_required(login_url="login")
def delete_all_selected(request):
    if is_normal_user(request):
        return redirect("web_login")
    model_name = request.POST.get('model_name')
    all_selected_id = request.POST.get("all_id")
    selected_id = all_selected_id.split(',')
    model_dict = {
        "User":User.objects.filter(id__in = selected_id).delete(),
        "ShopProduct":ShopProduct.objects.filter(id__in = selected_id).delete(),
        "ImagineProduct":ImagineProduct.objects.filter(id__in = selected_id).delete(),
        "Blog":Blog.objects.filter(id__in = selected_id).delete(),
        "ContactUsInquiry":ContactUsInquiry.objects.filter(id__in = selected_id).delete(),
        "ProductOrder":ProductOrder.objects.filter(id__in = selected_id).update(listing = False),
        "Newsletters": Newsletters.objects.filter(email__in = selected_id).delete(),  
        "BlogSubscriber": BlogSubscriber.objects.filter(id__in = selected_id).delete(),
        "BlogUser": BlogUser.objects.filter(id__in = selected_id).delete(),
        "BlogCategory": BlogCategory.objects.filter(id__in = selected_id).delete(),
        "BlogSubCategory": BlogSubCategory.objects.filter(id__in = selected_id).delete(),
        "Offer": Offer.objects.filter(id__in = selected_id).delete(),
        "UserGiftCard": UserGiftCard.objects.filter(id__in = selected_id).delete()
    }
    model_dict.get(model_name)
    return JsonResponse({"success": True, "message": "Deleted"})

@login_required(login_url="login")
def generate_pdf(request, subject):
    return generate_pdf_report(subject)

@login_required(login_url="login")
def generate_csv(request, subject): 
    return generate_csv_report(subject)   

def create_slug_of_shero_product(request):
    imagine_product = SheroDolls.objects.all()
    for i in imagine_product:
        slug = str(i.year)+i.name
        i.slug = slugify(slug)
        i.save()

def create_slug_of_imagine_product(request):
    imagine_product = ImagineProduct.objects.all()
    for i in imagine_product:
        slug = i.subcategory.name + '-' + i.name
        i.slug = slugify(slug)
        i.save()
      
def create_user_role(request):
    users = User.objects.all()
    for user in users:
        if not UserRole.objects.filter(user_id=user.id).exists():
            if SloperHospital.objects.filter(management_email = user.email).exists():
                UserRole.objects.create(user_id = user.id, role = "HOSPITAL")
            else:
                UserRole.objects.create(user_id = user.id, role = user.user_type)
    return JsonResponse({"Success": True})

