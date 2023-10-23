from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.conf import settings
from django.urls import reverse
from .manager import *
from .choices import *
import uuid
from datetime import timedelta
from re import sub
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save

class User(AbstractUser):
    username = None
    referral_code = models.CharField(max_length=50, unique=True, null=True)
    referral_reward_status = models.BooleanField(default=False)
    dolls_to_get_count = models.IntegerField(default= 0)
    dolls_got_count = models.IntegerField(default= 0)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE, default='CUSTOMER')
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=30, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    download_count = models.IntegerField(default= 0)
    download_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    profile_img = models.ImageField(upload_to="profile_image", null=True)
    is_mail_send = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    can_comment = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    wallet = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
    
    def increase_download_count(self):
        if self.download_count < 3:
            self.download_count += 1
            self.download_date = timezone.now()
            self.save()
                

class Module(models.Model):
    name = models.CharField(max_length=255, null=True)
    parent_id = models.CharField(max_length=255, null=True)
    add = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    view = models.BooleanField(default=False)
    is_child = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    url = models.CharField(max_length=255, null=True)
    icon = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name

class ModulePermission(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    add = models.BooleanField(default=False, null=True)
    edit = models.BooleanField(default=False, null=True)
    delete = models.BooleanField(default=False, null=True)
    view = models.BooleanField(default=False, null=True)

class EmailTemplate(models.Model):
    title = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=255, unique=True, null=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.subject

class MessageTemplate(models.Model):
    title = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=255, unique=True, null=True)
    content = models.TextField()

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.CharField(max_length=255, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    heading = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.CharField(max_length=255, null=True, blank=True)
    meta_keyword = models.CharField(max_length=255, null=True, blank=True)
    og_title = models.CharField(max_length=255, null=True, blank=True)
    og_description = models.CharField(max_length=255, null=True, blank=True)
    permalink = models.CharField(max_length=255, null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    banner_img = models.ImageField(upload_to="sub_category/%Y/%m/%d/", null=True)
    og_img = models.ImageField(upload_to="sub_category/%Y/%m/%d/", null=True)
    url = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class SocialMedia(models.Model):
    name = models.CharField(unique=True, max_length=255)
    icon = models.ImageField(upload_to="social_media", null = True)
    link = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DressType(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=2)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.CharField(max_length=255, null=True, blank=True)
    meta_keyword = models.CharField(max_length=255, null=True, blank=True)
    og_title = models.CharField(max_length=255, null=True, blank=True)
    og_description = models.CharField(max_length=255, null=True, blank=True)
    permalink = models.CharField(max_length=255, null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    og_img = models.ImageField(upload_to="dress_type/%Y/%m/%d/", null=True)
    url_slug = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class ProductCollection(models.Model):
    name = models.CharField(unique=True, max_length=255)
    priority = models.IntegerField(default=0)
    permalink = models.CharField(max_length=255, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProductColor(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=2)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(max_length=255, null=True, blank=True)
    detail_description = models.TextField(max_length=255, null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(max_length=255, null=True, blank=True)
    meta_keyword = models.CharField(max_length=255, null=True, blank=True)
    og_title = models.CharField(max_length=255, null=True, blank=True)
    og_description = models.TextField(max_length=255, null=True, blank=True)
    text_color = models.CharField(max_length=255, null=True, blank=True)
    image_color_code = models.CharField(max_length=255, null=True, blank=True)
    permalink = models.CharField(max_length=255, null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    thumbnail_img = models.ImageField(upload_to="product_color/%Y/%m/%d/", null=True)
    banner_img = models.ImageField(upload_to="product_color/%Y/%m/%d/", null=True)
    og_img = models.ImageField(upload_to="product_color/%Y/%m/%d/", null=True)
    url_slug = models.CharField(max_length=255, null=True, blank=True)

class BlogCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    
class BlogSubCategory(models.Model):
    name = models.CharField(max_length=255, unique=True )
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, null=True, blank=True)

class Blog(models.Model):
    blog_category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, null=True, blank=True)
    sub_category = models.ForeignKey(BlogSubCategory, on_delete=models.CASCADE, null=True, blank=True)
    heading = models.CharField(max_length=255)
    image = models.ImageField(upload_to="blog")
    content = models.TextField(null=True, blank=True)
    posted_by = models.CharField(max_length=255)
    video = models.FileField(upload_to="blog/video", null=True)
    other_important_info = models.TextField(null=True, blank=True)
    total_subscriber = models.IntegerField(default=0)
    is_publish = models.BooleanField(default=True)
    is_comment = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_blog_schedule = models.BooleanField(default=False)
    publish_at = models.DateTimeField(blank=True, null=True)
    shop = models.CharField(max_length=255, null=True)
    imagine = models.CharField(max_length=255, null=True)
    slug = models.CharField(max_length=255, null=True)
    # schedule_time = models.DateTimeField(auto_now=True ,null=True, blank=True)
    # is_active = models.BooleanField(default=True)
    # is_delete = models.BooleanField(default=False)
    def __str__(self):
        return self.heading

    def create_slug(self):
        slug_url = sub("[^A-Za-z0-9]+", "-", self.heading.lower())
        self.slug = sub("[--]{2}", "", slug_url)
        
        if self.slug[-1] == '-':
            self.slug = self.slug[0:-1]
    def remove_html_from_content(self):
        import bleach #type:ignore
        import re
        sanitized_content = bleach.clean(self.content, tags=[], strip=True)
        cleaned_content = re.sub(r'&\w+;', '', sanitized_content)
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
        import html
        decoded_content = html.unescape(cleaned_content)
        cleaned_content = " ".join(decoded_content.split())
        return cleaned_content      

    
class BlogComment(models.Model):
    comment = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="blog")
    created_at = models.DateTimeField(auto_now_add=True)

class BlogUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, null=True)
    comment = models.ForeignKey(BlogComment, on_delete=models.CASCADE, null=True)

class Country(models.Model):
    name = models.CharField(unique=True, max_length=255)
    heading = models.CharField(max_length=40)
    flag_img = models.ImageField(upload_to="country")
    map_img = models.ImageField(upload_to="country")
    initial_paragraph = models.TextField(null=True, blank=True)
    body_paragraph = models.TextField(null=True, blank=True)
    latitude = models.CharField(max_length=40, null=True, blank=True)
    longitude = models.CharField(max_length=40, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ShopProduct(models.Model):
    subcategory = models.ForeignKey(
                    SubCategory, on_delete=models.CASCADE, related_name="shop_product_subcategory"
    )
    product_collection = models.ForeignKey(
        ProductCollection,
        on_delete=models.CASCADE,
        related_name="shop_product_product_collection",
        null=True,
    )
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    slug = models.CharField(max_length=50, null=True, blank=True)
    unique_slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    alt_text = models.CharField(max_length=255)
    og_title = models.CharField(max_length=255)
    og_description = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField(null=True, blank=True)
    available_quantity = models.IntegerField(null=True, blank=True ,default=0)
    color = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    description_title = models.CharField(max_length=255, null=True, blank=True)
    country_title = models.CharField(max_length=255, null=True, blank=True)
    product_country_title = models.CharField(max_length=255, null=True, blank=True)
    #adding new field SKU
    sku = models.CharField(max_length=50, unique=True, blank=True)
    def discount_percentage(self):
        discount = self.original_price - self.offer_price
        return (discount / self.original_price) * 100

    def soft_delete(self):
        self.is_delete = True
        self.save()


# SIGNAL TRIGER WHEN NEW PRODUCT WILL BE SAVED 
@receiver(pre_save, sender=ShopProduct)
def generate_sku(sender, instance, **kwargs):
    if not instance.sku:
        # Generate SKU based on product name
        instance.sku = instance.name.replace(" ", "-").lower()


class ShopProductImage(models.Model):
    shop_product = models.ForeignKey(
        ShopProduct, on_delete=models.CASCADE, related_name="shop_product", null=True
    )
    primary_img = models.ImageField(
        upload_to="product/%Y/%m/%d/", null=True, blank=True
    )
    og_img = models.ImageField(upload_to="product/%Y/%m/%d/", null=True, blank=True)


class ShopProductImageSubTable(models.Model):
    shop_product_image = models.ForeignKey(
        ShopProductImage, on_delete=models.CASCADE, null=True
    )
    images = models.ImageField(upload_to="product/%Y/%m/%d/", null=True, blank=True)


class ImagineProduct(models.Model):
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name="imagine_product_subcategory",
    )
    dress_type = models.ForeignKey(
        DressType,
        on_delete=models.CASCADE,
        related_name="imagine_product_dress_type",
        null=True,
    )
    product_color = models.ForeignKey(
        ProductColor,
        on_delete=models.CASCADE,
        related_name="imagine_product_product_color",
        null=True,
    )
    name = models.CharField(max_length=255)
    alt_text = models.CharField(max_length=255)
    og_title = models.CharField(max_length=255)
    og_description = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    related_product_list = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=255, null=True, blank=True)
    unique_slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)

    def soft_delete(self):
        self.is_delete = True
        self.save()


class ImagineProductImage(models.Model):
    imagine_product = models.ForeignKey(
        ImagineProduct,
        on_delete=models.CASCADE,
        related_name="imagine_product",
        null=True,
    )
    primary_img = models.ImageField(
        upload_to="product/imagine/%Y/%m/%d/", null=True, blank=True
    )
    pdf_img = models.ImageField(
        upload_to="product/imagine/%Y/%m/%d/", null=True, blank=True
    )
    og_img = models.ImageField(
        upload_to="product/imagine/%Y/%m/%d/", null=True, blank=True
    )


class ImagineProductImageSubTable(models.Model):
    imagine_product_image = models.ForeignKey(
        ImagineProductImage, on_delete=models.CASCADE, null=True
    )
    images = models.ImageField(upload_to="product/%Y/%m/%d/", null=True, blank=True)

# need to remove
class OrderCharge(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    # percentage is in percent
    percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


# ------------ web_app
class Wishlist(models.Model):
    shop = models.ForeignKey(
        ShopProduct, on_delete=models.CASCADE, null=True, blank=True
    )
    imagine = models.ForeignKey(
        ImagineProduct, on_delete=models.CASCADE, null=True, blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Favorite(models.Model):
    imagine = models.ForeignKey(
        ImagineProduct, on_delete=models.CASCADE, null=True, blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class AnonymousCart(models.Model):
    a_id = models.BigIntegerField()
    shop_product_list = models.CharField(max_length=255, null=True, blank=True)
    last_active_time = models.DateTimeField(null=True, blank=True)


class AnonymousWishlist(models.Model):
    a_id = models.BigIntegerField()
    shop = models.ForeignKey(ShopProduct, on_delete=models.CASCADE)


class AnonymousFavorite(models.Model):
    a_id = models.BigIntegerField()
    imagine = models.ForeignKey(ImagineProduct, on_delete=models.CASCADE)


class Offer(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True)
    # type=models.CharField(max_length=250,null=True,blank=True)
    # amount in percentage
    percentage = models.FloatField(max_length=250, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    subcategory = models.CharField(max_length=250, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now=True)


class UsedOffer(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_used = models.BooleanField(default=False)


class UserCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, null=True)
    shop_product_list = models.CharField(max_length=255, null=True, blank=True)
    shero_dolls_list = models.CharField(max_length=255, null=True, blank=True)


# User's address start
class WebCountry(models.Model):
    short_name = models.CharField(max_length=3, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    phonecode = models.IntegerField()


class WebState(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    country = models.ForeignKey(WebCountry, on_delete=models.CASCADE)


class WebCity(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(WebState, on_delete=models.CASCADE)


class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    web_country = models.ForeignKey(
        WebCountry, on_delete=models.CASCADE, null=True, blank=True
    )
    web_state = models.ForeignKey(
        WebState, on_delete=models.CASCADE, null=True, blank=True
    )
    web_city = models.ForeignKey(
        WebCity, on_delete=models.CASCADE, null=True, blank=True
    )
    web_city = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    house_num = models.CharField(max_length=255, null=True, blank=True)
    area_name = models.CharField(max_length=255, null=True, blank=True)
    zip_code = models.CharField(max_length=255, null=True, blank=True)
    default_address = models.BooleanField(default=False, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
# User's address end

class ProductOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    order_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    card_brand = models.CharField(max_length=255, null=True, blank=True)
    # start shipping station
    carrier_service_name = models.CharField(max_length=255, null=True, blank=True)
    shipping_charge = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    # end shipping station   
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # total_amount = shipping_charge + tax + product subtotal
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_by_stripe = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_by_wallet = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_at = models.DateTimeField(auto_now_add=True, null=True)
    shipping_address = models.ForeignKey(UserAddress, on_delete=models.CASCADE, related_name="shipping", null=True)
    billing_address = models.ForeignKey(UserAddress, on_delete=models.CASCADE, related_name="billing", null=True)
    # order status = Completed, Canceled, Shipped, Accepted
    order_status = models.CharField(max_length=50, null=True, blank=True)
    is_refunded = models.BooleanField(default=False, null=True, blank=True)
    canceled_by = models.CharField(max_length=50, null=True, blank=True)
    canceled_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    listing = models.BooleanField(default=True, null=True, blank=True)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="offer", null=True)
    tracking_url = models.TextField(null=True, blank=True)
    webhook_data = models.JSONField(null=True, blank=True)
    
    def get_delivery_date(self):
        self.delivered_at = self.order_at + timedelta(days=settings.DELIVERY_DAYS)
        self.save()


class ProductOrderData(models.Model):
    shop_product = models.ForeignKey(ShopProduct, on_delete=models.CASCADE, null=True)
    product_order = models.ForeignKey(ProductOrder, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=0)
    per_unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)


# --------------end web_app
class Profile(models.Model):
    bio = models.CharField(max_length=255, default="", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)

# User's inquiry start 
class ContactUsInquiry(models.Model):
    name = models.CharField(max_length=255, null=True)
    email = models.EmailField(null=True)
    subject = models.CharField(max_length=255, null=True)
    inquiry = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    replied = models.BooleanField(default=False)
    reply = models.TextField(null=True)
    replied_at = models.DateTimeField(null=True)
    respondent_name = models.CharField(max_length=255, null=True)
    respondent_email = models.EmailField(null=True)


class ContectUsContent(models.Model):
    heading = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    image = models.ImageField(upload_to="contect_us_content/%Y/%m/%d/", null=True)


class BlogContent(models.Model):
    heading = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    image = models.ImageField(upload_to="blog_content/%Y/%m/%d/", null=True)    

# User's inquiry end


# Contact us details start
class ContactUsDetails(models.Model):
    email = models.EmailField(null=True)
    mobile = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    is_delete = models.BooleanField(default=False)
    latitude = models.CharField(max_length=40, null=True, blank=True)
    longitude = models.CharField(max_length=100, null=True, blank=True)
    default_address = models.BooleanField(default=False, null=True, blank=True)
# Contact us details end

# OrderDetail Model is saving stripe response after order successfully placed and payment successfully done
class OrderDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_order = models.ForeignKey(ProductOrder, on_delete=models.CASCADE, null=True)
    stripe_charge_id = models.CharField(max_length=255, null=True, blank=True)  # which is start with ch
    balance_transaction = models.CharField(max_length=255, null=True, blank=True)
    amount = models.IntegerField(verbose_name="Amount")
    payment_method = models.CharField(max_length=255, null=True, blank=True)
    reciept_url = models.CharField(max_length=255, null=True, blank=True)
    has_paid = models.BooleanField(default=False, verbose_name="Payment Status")
    status = models.CharField(max_length=255, null=True, blank=True)
    payment_intent = models.CharField(max_length=255, null=True, blank=True)
    payment_method_types = models.CharField(max_length=255, null=True, blank=True)
    customer = models.CharField(max_length=255, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

# Blog subscriber start
class BlogSubscriber(models.Model):
    email = models.EmailField(null=True)
# Blog subscriber end    


class Newsletters(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.CharField(max_length=255)
    msg = models.CharField(max_length=500, null=True, blank=True)
    created = models.DateField(auto_now_add=True)


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shopproduct = models.ForeignKey(
        ShopProduct, on_delete=models.CASCADE, null=True, blank=True
    )
    user_review = models.CharField(max_length=250, null=True, blank=True)
    rating = models.FloatField(max_length=250, null=True, blank=True)


class TermsCondition(models.Model):
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)


class privacy(models.Model):
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)


class Legal(models.Model):
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)


class Shipping(models.Model):
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)


class FAQ(models.Model):
    Questions = models.TextField(null=True, blank=True)
    Answers = models.TextField(null=True, blank=True)


class Slider(models.Model):
    title = models.CharField(max_length=250, null=True, blank=True)
    content = models.CharField(max_length=250, null=True, blank=True)
    image = models.ImageField(upload_to="slider_type/%Y/%m/%d/", null=True)


class ProductShop(models.Model):
    title = models.CharField(max_length=250, null=True, blank=True)
    content = models.CharField(max_length=250, null=True, blank=True)
    image = models.ImageField(upload_to="product_shop_type/%Y/%m/%d/", null=True)


class Subscription(models.Model):
    title = models.CharField(max_length=250, null=True, blank=True)
    content = models.CharField(max_length=250, null=True, blank=True)
    image = models.ImageField(upload_to="subscription_type/%Y/%m/%d/", null=True)


class GiftCard(models.Model):
    gift_price = models.IntegerField(default=0)
    # days after gift card expire like 90 days after that gift card expire
    days = models.IntegerField(default=0, blank=True, null=True)

class GiftCardType(models.Model):
    giftcard_type = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    

class GiftCardTypeImages(models.Model):
    giftcard_type = models.ForeignKey(GiftCardType, on_delete=models.CASCADE, blank=True, null=True)
    images = models.ImageField(upload_to="giftcard_type/%Y/%m/%d/", null=True, blank=True)
    

# Shero Subscription Plan Start
class SubscriptionPlanBenefits(models.Model):
    title = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)

class SubscriptionPlan(models.Model):
    # plan type = Monthly, Quarterly, Bi-Annual, Annual 
    plan_type = models.CharField(max_length=50, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Stripe Price Id and plan Id
    subscription_price_id = models.CharField(max_length=255, null=True, blank=True)
    plan_id = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    sort_order = models.IntegerField(null=True)
    # validity = models.CharField(max_length=50, null=True, blank=True)
    def discount_on_plan_percentage(self):
        discount = self.original_price - self.offer_price
        return (discount / self.original_price) * 100

class SubscriptionPlanAndBenefits(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    benefit = models.ForeignKey(SubscriptionPlanBenefits, on_delete=models.CASCADE)
 
# Shero Subscription End

class UserGiftCard(models.Model):
    GIFT_CARD_TYPE_CHOICES = (
        ('GIFT_CARD', 'GIFT_CARD'),
        ('SHERO_SUBSCRIPTION_GIFT_CARD', 'SHERO_SUBSCRIPTION_GIFT_CARD'),
    )
    # if customer purchase gift card with admin created gift card amount else null
    gift_card = models.ForeignKey(GiftCard, on_delete=models.CASCADE, blank=True, null=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, blank=True, null=True)
    giftcard_image = models.ForeignKey(GiftCardTypeImages, on_delete=models.CASCADE, blank=True, null=True)
    receiver_email = models.CharField(max_length=255, null=True)
    sender_email = models.CharField(max_length=255, null=True)
    receiver_name = models.CharField(max_length=255, null=True)
    gift_code = models.CharField(max_length=255, unique=True, null=True)
    title = models.CharField(max_length=255, null=True)
    user_message = models.TextField(null=True)
    gift_card_type = models.CharField(max_length=255, choices=GIFT_CARD_TYPE_CHOICES, null=True, default='GIFT_CARD')
    is_used = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    payment_intent_id = models.CharField(max_length=255, null=True)
    stripe_charge_id = models.CharField(max_length=255, null=True)
    balance_transaction = models.CharField(max_length=255, null=True)
    amount = models.CharField(max_length=255, null=True)
    payment_method = models.CharField(max_length=255, null=True)
    reciept_url = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, null=True)
    payment_intent = models.CharField(max_length=255, null=True)
    payment_method_types = models.CharField(max_length=255, null=True)
    customer = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)
    expire_at = models.DateTimeField(blank=True, null=True)
    
    def expiry_date(self):
        if self.gift_card_id:
            days = self.gift_card.days
        else:
            days = 30
        self.expire_at = self.created_at + timedelta(days)
        self.save()


class TransactionGiftCard(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('GIFT_CARD', 'GIFT_CARD'),
        ('SHERO_SUBSCRIPTION_GIFT_CARD', 'SHERO_SUBSCRIPTION_GIFT_CARD'),
    )
    gift_card=models.ForeignKey(UserGiftCard, on_delete=models.CASCADE, null=True, blank=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    type_transaction = models.IntegerField(choices=TRANSACTION_TYPE_CHOICES, default="GIFT_CARD")   
    order=models.IntegerField(null=True,blank=True)
    created_date=models.DateField(auto_now_add=True)
    less_price=models.DecimalField(decimal_places=2, max_digits=7,null=True,blank=True)
    add_price=models.DecimalField(decimal_places=2, max_digits=7,null=True,blank=True)


class ProductImagine(models.Model):
    title = models.CharField(max_length=250, null=True, blank=True)
    content = models.CharField(max_length=250, null=True, blank=True)
    image = models.ImageField(upload_to="product_image_type/%Y/%m/%d/", null=True)

# links on blog start
class LinksOnBlog(models.Model):
    title = models.CharField(max_length=50, null=True, blank=True)
    image = models.ImageField(upload_to="links_on_blog_image", null=True)
    is_active = models.BooleanField(default=True)
    url = models.CharField(max_length=255, unique=True, null=True)
    is_social = models.BooleanField(default=False)# this column is to distinguish between social media link and other link
# links on blog end    


class SheroDolls(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    claim_to_fame = models.CharField(max_length=50, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    month = models.CharField(max_length=50, null=True, blank=True)
    year = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    is_publish = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    publish_at = models.DateTimeField(blank=True, null=True)
    quantity = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    features = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=50, null=True, blank=True) 
    unique_slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    og_title = models.CharField(max_length=255, null=True, blank=True) 
    og_description = models.CharField(max_length=255, null=True, blank=True) 
    
class SheroDollsImage(models.Model):
    shero_dolls = models.ForeignKey(SheroDolls, on_delete=models.CASCADE, related_name="shero_dolls", null=True)
    primary_img = models.ImageField(upload_to="shero_dolls/%Y/%m/%d/", null=True, blank=True)
    og_img = models.ImageField(upload_to="shero_dolls/%Y/%m/%d/", null=True, blank=True)

class SheroDollsImageSubTable(models.Model):
    shero_dolls_image = models.ForeignKey(SheroDollsImage, on_delete=models.CASCADE, null=True)
    images = models.ImageField(upload_to="shero_dolls/%Y/%m/%d/", null=True, blank=True)


class UserSubscriptions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    shero_subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    # stripe customer Id and subscription Id
    customer_id = models.CharField(max_length=255,null=True,blank=True)
    subscription_id = models.CharField(max_length=255,null=True,blank=True)
    start_at = models.DateField(blank=True, null=True)
    expire_at = models.DateField(blank=True, null=True)
    is_delete = models.BooleanField(default=False)

class UserSubscriberHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    plan_type = models.CharField(max_length=255,null=True,blank=True)
    subscription_id = models.CharField(max_length=255,null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_at = models.DateField(blank=True, null=True)
    expire_at = models.DateField(blank=True, null=True)
    status = models.BooleanField(default=False)
    canceled = models.BooleanField(default=False)
    canceled_at = models.DateField(blank=True, null=True)

class SubscriptionTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    # start_at = models.DateField(blank=True, null=True)
    # expire_at = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, null=True, blank=True)

class GiftCardImage(models.Model):
    title=models.CharField(max_length=250,null=True,blank=True)
    giftcard_image=models.ImageField(upload_to="gift_card/%Y/%m/%d/", null=True, blank=True)

class RecentlyVisitedItems(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(ShopProduct, on_delete=models.CASCADE, null=True)
    visited_at = models.DateTimeField(auto_now_add=True)


# User referral start
class UserReferral(models.Model):
    user_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_from", null=True)
    user_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_to", null=True)
    order = models.ForeignKey(ProductOrder, on_delete=models.CASCADE, null=True)
    order_status = models.BooleanField(default=False)  
    is_delete = models.BooleanField(default=False)    
# User referral end

class UserAndOrderBackup(models.Model):
    user_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    order_id = models.CharField(max_length=255, null=True, blank=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    order_at = models.DateTimeField(auto_now_add=True, null=True)
    quantity = models.IntegerField(default=0)
    per_unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )

class WalletTransaction(models.Model):
    AMOUNT_STATUS_CHOICES = (
        ('DEPOSIT', 'DEPOSIT'),
        ('WITHDRAW', 'WITHDRAW'),
    )
    TRANSACTION_TYPE_CHOICES = (
        ('GIFTCARD', 'GIFTCARD'),
        ('PAYMENT', 'PAYMENT')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # amount => which deduct or add in wallet
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # remaining_wallet_balance => show wallet balance after adding or deducting amount from it
    remaining_wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # amount status =>  withdraw or deposit status
    amount_status = models.CharField(max_length=255, choices=AMOUNT_STATUS_CHOICES, null=True, default='DEPOSIT')
    # transaction_type => how amount deducted or added in wallet
    transaction_type = models.CharField(max_length=255, choices=TRANSACTION_TYPE_CHOICES, null=True, default='GIFTCARD')
    transaction_at = models.DateTimeField(auto_now_add=True, null=True)


class SloperTemplate(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="sloper/template/%Y/%m/%d/", null=True, blank=True)
    status = models.BooleanField(default=False)

class SloperTexture(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="sloper/texture/%Y/%m/%d/", null=True, blank=True)
    status = models.BooleanField(default=False)

class SloperElement(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="sloper/element/%Y/%m/%d/", null=True, blank=True)
    status = models.BooleanField(default=False)  

class SloperMulticolorIconSVG(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="sloper/svg/%Y/%m/%d/", null=True, blank=True)
    status = models.BooleanField(default=False)

    def get_svg_data(self):
        return self.image.read().decode()

    def delete(self):
        self.image.delete()
        super().delete()

class Notification(models.Model):
    NOTIFICATION_CHOICES = (
        ('REFERRER', 'REFERRER'),
        ('INQUIRY', 'INQUIRY')   
    ) 
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    sender = models.EmailField(null=True, blank=True)
    receiver = models.EmailField(null=True, blank=True)
    recevied_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    message = models.CharField(max_length=255, null=True, blank=True)
    notification_type = models.CharField(max_length=255, choices=NOTIFICATION_CHOICES, null=True, blank=True)
    

class AboutUs(models.Model):
    heading_1 = models.CharField(max_length=255, null=True, blank=True)
    image_1 = models.ImageField(upload_to="about_us/image_1/%Y/%m/%d/", null=True, blank=True) 
    content_1 = models.TextField(null=True)
    heading_2 = models.CharField(max_length=255, null=True, blank=True)
    image_2 = models.ImageField(upload_to="about_us/image_2/%Y/%m/%d/", null=True, blank=True) 
    content_2 = models.TextField(null=True)
    heading_3 = models.CharField(max_length=255, null=True, blank=True)
    content_3 = models.TextField(null=True)
    heading_4 = models.CharField(max_length=255, null=True, blank=True)
    image_4 = models.ImageField(upload_to="about_us/image_4/%Y/%m/%d/", null=True, blank=True) 
    content_4 = models.TextField(null=True)
    heading_5 = models.CharField(max_length=255, null=True, blank=True)
    content_5 = models.TextField(null=True)


class SheroSubscriptionContent(models.Model):
    banner_image = models.ImageField(upload_to="shero_subscription_content/banner_image/%Y/%m/%d/", null=True, blank=True)
    banner_image_content = models.TextField(null=True)
    intro_paragraph = models.TextField(null=True)
    shero_benefits_title = models.TextField(null=True)
    shero_benefits_image_1 = models.ImageField(upload_to="shero_subscription_content/shero_benefits_image_1/%Y/%m/%d/", null=True, blank=True)
    shero_benefits_content_1 = models.TextField(null=True)
    shero_benefits_image_2 = models.ImageField(upload_to="shero_subscription_content/shero_benefits_image_2/%Y/%m/%d/", null=True, blank=True)
    shero_benefits_content_2 = models.TextField(null=True)
    shero_benefits_image_3 = models.ImageField(upload_to="shero_subscription_content/shero_benefits_image_3/%Y/%m/%d/", null=True, blank=True)
    shero_benefits_content_3 = models.TextField(null=True)
    shero_benefits_image_4 = models.ImageField(upload_to="shero_subscription_content/shero_benefits_image_4/%Y/%m/%d/", null=True, blank=True)
    shero_benefits_content_4 = models.TextField(null=True)
    shero_benefits_image_5 = models.ImageField(upload_to="shero_subscription_content/shero_benefits_image_5/%Y/%m/%d/", null=True, blank=True)
    shero_benefits_content_5 = models.TextField(null=True)
    shero_how_it_works_title = models.CharField(max_length=255, null=True, blank=True) 
    shero_how_it_works_title_1 = models.CharField(max_length=255, null=True, blank=True)
    shero_how_it_works_content_1 = models.TextField(null=True)
    shero_how_it_works_image_1 = models.ImageField(upload_to="shero_subscription_content/shero_how_it_works_image_1/%Y/%m/%d/", null=True, blank=True)
    shero_how_it_works_title_2 = models.CharField(max_length=255, null=True, blank=True)
    shero_how_it_works_content_2 = models.TextField(null=True)
    shero_how_it_works_image_2 = models.ImageField(upload_to="shero_subscription_content/shero_how_it_works_image_2/%Y/%m/%d/", null=True, blank=True)
    shero_how_it_works_title_3 = models.CharField(max_length=255, null=True, blank=True)
    shero_how_it_works_content_3 = models.TextField(null=True)
    shero_how_it_works_image_3 = models.ImageField(upload_to="shero_subscription_content/shero_how_it_works_image_3/%Y/%m/%d/", null=True, blank=True)
    shero_how_it_works_title_4 = models.CharField(max_length=255, null=True, blank=True)
    shero_how_it_works_content_4 = models.TextField(null=True)
    shero_how_it_works_image_4 = models.ImageField(upload_to="shero_subscription_content/shero_how_it_works_image_4/%Y/%m/%d/", null=True, blank=True)
    create_play_image = models.ImageField(upload_to="shero_subscription_content/create_play_image/%Y/%m/%d/", null=True, blank=True)
    invite_your_friend_image = models.ImageField(upload_to="shero_subscription_content/invite_your_friend_image/%Y/%m/%d/", null=True, blank=True)

class ReferralContent(models.Model):
    image = models.ImageField(upload_to="referral/image/%Y/%m/%d/", null=True, blank=True) 
    content = models.TextField(null=True)


class TokenAndSecretKey(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)
    
# class GiftedSheroSubscription(models.Model):
#     subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, blank=True, null=True)
#     user_gift_card = models.ForeignKey(UserGiftCard, on_delete=models.CASCADE, blank=True, null=True)
#     # stripe customer id
#     customer_id = models.CharField(max_length=255, null=True, blank=True)
#     sub_start_at = models.DateField(null=True, blank=True)
#     sub_end_at = models.DateField(null=True, blank=True)
#     gift_buy_at = models.DateField(auto_now_add=True, null=True, blank=True)
#     gift_expire_at = models.DateField(null=True, blank=True)
    
#     # set date after one month from gift_buy_at
#     def set_expiry_date(self):
#         self.gift_expire_at = self.gift_buy_at + relativedelta(months=1)
#         self.save()
        
class GuestUserData(models.Model):
    email = models.CharField(max_length=255, null=True, blank=True)
    order_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    carrier_code = models.CharField(max_length=255, null=True, blank=True)
    carrier_service_name = models.CharField(max_length=255, null=True, blank=True)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # total_amount is the amount of product excluding tax and shipping_charge
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_status = models.CharField(max_length=50, null=True, blank=True)
    tracking_url = models.TextField(null=True, blank=True)
    # order_detail example => [{ id: 1, quantity: 4, per_unit_price: 4 }]
    order_detail = models.JSONField(null=True)
    shipping_address = models.JSONField(null=True)
    billing_address = models.JSONField(null=True)
    webhook_data = models.JSONField(null=True)
    stripe_payment_data = models.JSONField(null=True)
    order_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    
    def get_delivery_date(self):
        return self.order_at + timedelta(days=settings.DELIVERY_DAYS)

class BaseSlug(models.Model):
    slug = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    class Meta:
        abstract = True 

class BaseTitleAndDescription(BaseSlug):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True 

class SloperLandingPageBannerImage(BaseSlug):
    banner_img = models.ImageField(upload_to="sloper_landing_page/banner_images/%Y/%m/%d/", null=True, blank=True)

class SloperLandingPageHowItWork(BaseTitleAndDescription):
    pass

class SloperLandingPageHowItWorkSection(BaseSlug):
    img = models.ImageField(upload_to="sloper_landing_page/how_it_work_section_images/%Y/%m/%d/", null=True, blank=True)
    description = models.TextField(null=True, blank=True)

class SloperLandingPageTestimonial(BaseTitleAndDescription):
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    review_count = models.IntegerField(default=0)

class SloperLandingPageTestimonialSection(BaseSlug):
    img = models.ImageField(upload_to="sloper_landing_page/testimonial_images/%Y/%m/%d/", null=True, blank=True)
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

class SloperUserFolder(BaseSlug):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder_name = models.CharField(max_length=255, null=True, blank=True)
    is_trash = models.BooleanField(default=False)

    def restore_folder_function_url(self):
        return reverse('restore_folder', kwargs={'slug':self.slug})
class SloperUserDesign(BaseSlug):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    folder = models.ForeignKey(SloperUserFolder, on_delete=models.CASCADE, null=True, blank=True)
    is_trash = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now=True)

    def restore_design_function_url(self):
        return reverse('restore_design', kwargs={'slug':self.slug})

class SloperPlanCategory(BaseSlug):
    name = models.CharField(max_length=255, null=True)
    category_title = models.CharField(max_length=55, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now_add=True)

class SloperBasicPrice(BaseSlug):
    category = models.ForeignKey(SloperPlanCategory, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255, null=True)
    # price - this field is for the price of patient, teachet, student, individual month plan, and discount on school plan 
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now_add=True)

class SloperPlan(BaseSlug):
    category = models.ForeignKey(SloperPlanCategory, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255, null=True)
    from_user = models.IntegerField(default=1)
    upto_user = models.IntegerField(default=1)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

class SloperStripeData(BaseSlug):
    email = models.EmailField(null=True)
    # transaction_id = models.CharField(max_length=255, null=True)
    stripe_product_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
    reciept_url = models.CharField(max_length=255, null=True, blank=True)
    # subscription_id is inserted when schedule_subscription_webhook call
    subscription_id = models.CharField(max_length=255, null=True, blank=True)
    schedule_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_data = models.JSONField(null=True)

class SloperBillingAddress(BaseSlug):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)

class UserSloperSubscription(BaseSlug):
    # category = Individual, Hospital, School
    category = models.CharField(max_length=255, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    sloper_stripe_data = models.ForeignKey(SloperStripeData, on_delete=models.CASCADE, null=True)
    # user_plan_detail_id containd id of "UserIndividualPlan", "UserHospitalPlan" and "UserSchoolPlan" to get plan details
    plan_detail = models.JSONField(null=True, blank=True) 
    is_recurring = models.BooleanField(default=True)
    purchased_at = models.DateTimeField(auto_now_add=True)    
    start_at = models.DateTimeField(null=True)
    end_at = models.DateTimeField(null=True)
    is_ended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    billing_address = models.ForeignKey(SloperBillingAddress, on_delete=models.CASCADE, null=True)
    is_canceled = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True)
    is_gifted = models.BooleanField(default=True)
   
    def cancel_subscription_url(self):
        return reverse('cancel_sloper_subscription', kwargs={'slug': self.slug})

    def activate_subscription_url(self):
        return reverse('activate_sloper_subscription', kwargs={'slug': self.slug})
       
class UserGiftSloperPlan(BaseSlug):
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # user_detail field respective to its category 
    # "Individual" = recipient_name
    # "Hospital" = hospital_name, hospital_data.name, management_name, hospital_address, phone_number
    # "School" = school_name, hospital_data.name, management_name, hospital_address, phone_number
    user_detail = models.JSONField(null=True, blank=True)
    receiver_email = models.EmailField(null=True) 
    is_wasted = models.BooleanField(default=False)
    user_sloper_subscription = models.ForeignKey(UserSloperSubscription, on_delete=models.CASCADE, null=True)
                                                    
                                                            
                                                            

class SloperHospital(BaseSlug):
    name = models.CharField(max_length=255, null=True)
    management_name = models.CharField(max_length=255, null=True)
    management_email = models.EmailField(null=True)
    street = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, null=True)
    zipcode = models.CharField(max_length=255, null=True)
    phone_number = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField(default=True)

    def summery_sloper_hospital_plan_function_url(self):
        return reverse('summery_sloper_hospital_plan', kwargs={'hospital_name': self.name, 'slug':self.slug})


class SloperSchool(BaseSlug):
    name = models.CharField(max_length=255, null=True)
    management_name = models.CharField(max_length=255, null=True)
    management_email = models.EmailField(null=True)
    street = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    country = models.CharField(max_length=255, null=True)
    zipcode = models.CharField(max_length=255, null=True)
    phone_number = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField(default=True)

    def summery_sloper_school_plan_function_url(self):
        return reverse('summery_sloper_school_plan', kwargs={'school_name': self.name, 'slug':self.slug})


class HospitalRegisteredPatients(BaseSlug):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    hospital = models.ForeignKey(SloperHospital, on_delete=models.CASCADE, null=True)
    has_subscription = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)    



class HospitalUnregisteredPatients(BaseSlug):
    email = models.EmailField(null=True, blank=True)
    hospital = models.ForeignKey(SloperHospital, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255, null=True)
    phone_number = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)    


class UserSchoolPlan(BaseSlug):
    category = models.ForeignKey(SloperPlanCategory, on_delete=models.CASCADE, null=True)
    price_per_student = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_per_teacher = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    no_of_student = models.IntegerField(null=True, blank=True)
    no_of_teacher = models.IntegerField(null=True, blank=True)  
    user_count_details = models.JSONField(null=True, blank=True)    


class ShippingPrice(BaseSlug):
    order_value_from = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_value_upto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class UserRole(BaseSlug):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # role = "SUPERADMIN", "SUBADMIN", "CUSTOMER", "HOSPITAL", "SCHOOL"
    role = models.CharField(max_length=50, null=True)
    

@receiver(post_delete, sender=User)
@receiver(post_delete, sender=SubCategory)
@receiver(post_delete, sender=SocialMedia)
@receiver(post_delete, sender=DressType)
@receiver(post_delete, sender=ProductColor)
@receiver(post_delete, sender=Blog)
@receiver(post_delete, sender=Country)
@receiver(post_delete, sender=ShopProductImage)
@receiver(post_delete, sender=ShopProductImageSubTable)
@receiver(post_delete, sender=ImagineProductImage)
@receiver(post_delete, sender=ImagineProductImageSubTable)
@receiver(post_delete, sender=ContectUsContent)
@receiver(post_delete, sender=BlogContent)
@receiver(post_delete, sender=Slider)
@receiver(post_delete, sender=ProductShop)
@receiver(post_delete, sender=Subscription)
@receiver(post_delete, sender=GiftCardTypeImages)
@receiver(post_delete, sender=ProductImagine)
@receiver(post_delete, sender=LinksOnBlog)
@receiver(post_delete, sender=SheroDollsImage)
@receiver(post_delete, sender=SheroDollsImageSubTable)
@receiver(post_delete, sender=GiftCardImage)
@receiver(post_delete, sender=SloperTemplate)
@receiver(post_delete, sender=SloperTexture)
@receiver(post_delete, sender=SloperElement)
@receiver(post_delete, sender=SloperMulticolorIconSVG)
@receiver(post_delete, sender=AboutUs)
@receiver(post_delete, sender=SheroSubscriptionContent)
@receiver(post_delete, sender=ReferralContent)
@receiver(post_delete, sender=SloperLandingPageBannerImage)
@receiver(post_delete, sender=SloperLandingPageHowItWorkSection)
@receiver(post_delete, sender=SloperLandingPageTestimonialSection)
def delete_img_on_delete(sender, instance, **kwargs):
    for i in instance._meta.get_fields():
        if i.__class__.__name__ in ['ImageField', 'FileField']:
            file = getattr(instance, i.name)
            file.delete(save=False)


@receiver(pre_save, sender=User)
@receiver(pre_save, sender=SubCategory)
@receiver(pre_save, sender=SocialMedia)
@receiver(pre_save, sender=DressType)
@receiver(pre_save, sender=ProductColor)
@receiver(pre_save, sender=Blog)
@receiver(pre_save, sender=Country)
@receiver(pre_save, sender=ShopProductImage)
@receiver(pre_save, sender=ShopProductImageSubTable)
@receiver(pre_save, sender=ImagineProductImage)
@receiver(pre_save, sender=ImagineProductImageSubTable)
@receiver(pre_save, sender=ContectUsContent)
@receiver(pre_save, sender=BlogContent)
@receiver(pre_save, sender=Slider)
@receiver(pre_save, sender=ProductShop)
@receiver(pre_save, sender=Subscription)
@receiver(pre_save, sender=GiftCardTypeImages)
@receiver(pre_save, sender=ProductImagine)
@receiver(pre_save, sender=LinksOnBlog)
@receiver(pre_save, sender=SheroDollsImage)
@receiver(pre_save, sender=SheroDollsImageSubTable)
@receiver(pre_save, sender=GiftCardImage)
@receiver(pre_save, sender=SloperTemplate)
@receiver(pre_save, sender=SloperTexture)
@receiver(pre_save, sender=SloperElement)
@receiver(pre_save, sender=SloperMulticolorIconSVG)
@receiver(pre_save, sender=AboutUs)
@receiver(pre_save, sender=SheroSubscriptionContent)
@receiver(pre_save, sender=ReferralContent)
@receiver(pre_save, sender=SloperLandingPageBannerImage)
@receiver(pre_save, sender=SloperLandingPageHowItWorkSection)
@receiver(pre_save, sender=SloperLandingPageTestimonialSection)
def delete_img_on_change(sender, instance, **kwargs):
    if not instance.id:
        return False

    try:
        obj = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        return False

    for i in instance._meta.get_fields():
        if i.__class__.__name__ in ['ImageField', 'FileField']:
            field_name = i.name
            old_file = getattr(obj, field_name)
            new_file = getattr(instance, field_name)
            if old_file and not old_file == new_file:
                old_file.delete(save=False)
                