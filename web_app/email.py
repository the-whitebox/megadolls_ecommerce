from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import send_mail
from adminpanel.models import EmailTemplate, User, ProductOrder, OrderDetail, GuestUserData
from .encryption_util import text_encryption

EMAIL_FROM = settings.EMAIL_HOST_USER

def verify_mail(user):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    encrptyed_user_id = text_encryption(user.id)
    link = f'{settings.SITE_URL}web_verify_mail/{encrptyed_user_id}'
    email_template = EmailTemplate.objects.get(title='User Verification')
    subject = email_template.subject
    content = email_template.content
    merge_data = {'link': link, 'content': content, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}   
    html_message = render_to_string("email_html/account-signup-verification.html", merge_data)  
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_FROM, [user.email], fail_silently=False, html_message=html_message)


def welcome_mail_for_signing_up(email, name):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    email_data = EmailTemplate.objects.get(title = "Welcome To Megadolls")
    content = email_data.content
    merge_data = {'name': name, "content": content, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}   
    html_message = render_to_string("email_html/welcome.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def otp_to_reset_password(otp, email, link):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    email_data = EmailTemplate.objects.get(title = "OTP To Reset Password")
    content = email_data.content
    merge_data = {'otp': otp, 'content': content, "link": link, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}  
    html_message = render_to_string("email_html/forgot-password.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def blog_subscription_confirmation(email):
    blog_link = f'{settings.SITE_URL}meaningful-play'
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    encrptyed_email = text_encryption(email)
    unsubscribe_link = f'{settings.SITE_URL}unsubscribe-to-blog/{encrptyed_email}/'
    email_data = EmailTemplate.objects.get(title = "Thank You For Subscribing To Our Blogs")
    content = email_data.content  
    merge_data = {'content': content, 'email': email, 'unsubscribe_link': unsubscribe_link, 'blog_link' : blog_link, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/subscribe_to_blog.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def newsletter_confirmation(email):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    encrptyed_email = text_encryption(email)
    unsubscribe_link = f'{settings.SITE_URL}unsubscribe-to-newsletter/{encrptyed_email}/'
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        subscriber_name = user.name
    else:
        subscriber_name = "Megadolls User"
    email_data = EmailTemplate.objects.get(title = "Newsletter Confirmation")
    content = email_data.content
    merge_data = {'content': content, 'email': email, "subscriber_name": subscriber_name, 'unsubscribe_link': unsubscribe_link, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/subscribe-to-our-newsletter.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def shero_dolls_subscription_confirmation(email, name):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    email_data = EmailTemplate.objects.get(title = "Shero Dolls Subscription Confirmation")
    content = email_data.content
    merge_data = {'content': content, 'name': name, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/shero-subscription-confirmation.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)  


def send_mail_subscription_cancel(email, name):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    email_data = EmailTemplate.objects.get(title = "Shero Dolls Subscription Cancel")
    content = email_data.content
    merge_data = {'content': content, 'name': name, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/shero-subscription-cancellation.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def send_mail_giftcard(img_url='', receiver_email='', sender_email='', sender_message=''):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    redeem_gift_card_link = f'{settings.SITE_URL}redeem_my_gift_card/'
    email_data = EmailTemplate.objects.get(title='Gift Card')
    content = email_data.content
    merge_data = {'content': content, 'img_url': img_url, 'sender_email': sender_email, 'sender_message': sender_message, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link, 'redeem_gift_card_link': redeem_gift_card_link}
    html_message = render_to_string("email_html/gift-card-recipient.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [receiver_email], fail_silently=False, html_message=html_message)


def send_mail_giftcard_sender(receiver_email, sender_email, receipt_url, gift_card=None, sender_name='Megadolls User'):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'

    email_data = EmailTemplate.objects.get(title='Sender Mail To Send Gift Someone')
    content = email_data.content    
    merge_data = {'content': content, 'receiver_email': receiver_email, 'receipt': receipt_url, 'gift_card': gift_card, "sender_name": sender_name, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/gift-card-sender.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [sender_email], fail_silently=False, html_message=html_message)


def send_mail_shero_subscription_gift_recipient(subscription_plan='', receiver_email='', sender_email='', sender_message=''):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    if User.objects.filter(email=sender_email).exists():
        user = User.objects.get(email=sender_email)
        sender_name = user.name
    else:
        sender_name = sender_email
    subject = "You Received A Shero Subscription as Gift"
    merge_data = {'subscription_plan': subscription_plan, 'sender_email': sender_email, 'sender_message': sender_message, 'receiver_email':receiver_email, 'sender_name': sender_name, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/shero-gift-subscription-recipient.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_FROM, [receiver_email], fail_silently=False, html_message=html_message)


def send_mail_shero_subscription_gift_sender(subscription_plan, receiver_email, sender_email, receipt_url, sender_name):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'

    subject = "You Gifted A Shero Subscription"
    merge_data = {'subscription_plan': subscription_plan, 'receiver_email': receiver_email, 'receipt': receipt_url, 'sender_name': sender_name, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link }
    html_message = render_to_string("email_html/shero-gift-subscription-sender.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_FROM, [sender_email], fail_silently=False, html_message=html_message)


def send_redeem_otp(user, otp):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    email_data = EmailTemplate.objects.get(title='Gift Card otp')
    content = email_data.content
    merge_data = {'content': content, 'otp': str(otp), 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/otp_to_redeem_giftcard.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [user.email], fail_silently=False, html_message=html_message)


def send_mail_order_place(email, order_id, order_date, amount_dict, is_user_authenticated, product_order=None):
    encrptyed_order_id = text_encryption(order_id)
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        sender_name = user.name
        receipt_url = f'{settings.SITE_URL}registered-user-reciept/{encrptyed_order_id}'
    else:
        receipt_url = f'{settings.SITE_URL}guest-user-reciept/{encrptyed_order_id}'
        sender_name = "Megadolls User"
    subject = "Megadolls Order Placed"
    merge_data = {'receipt_url': receipt_url, 'sender_name': sender_name, 'order_id': order_id, 'order_date': order_date, 'is_user_authenticated': is_user_authenticated, 'product_order': product_order, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/order-confirmation.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def cancel_order(email, name, order_id):
    product_order = ProductOrder.objects.get(order_id = order_id)
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    email_data = EmailTemplate.objects.get(title='Order Cancel')
    content = email_data.content
    merge_data = {'product_order':product_order, 'content': content, 'order_id': order_id, 'name': name, 'subject': email_data.subject, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/order-cancellation.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def send_mail_for_order_shipped(email, order_id, tracking_url=None):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    if not tracking_url:
        tracking_url = ''
    email_data = EmailTemplate.objects.get(title='Order Shipped')
    if not tracking_url:
        tracking_url = ''
    content = email_data.content
    merge_data = {'content': content, 'order_id':order_id, 'tracking_url':tracking_url, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_html/order_shipped.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(email_data.subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)


def send_mail_plan_discontinue(emails:list):
    email_template = EmailTemplate.objects.get(title='Shero Subscription Plan Discontinue')
    subject = email_template.subject
    message = email_template.content
    plain_text = strip_tags(message)
    send_mail(subject, plain_text, EMAIL_FROM, emails, fail_silently=False)


def mail_send_verify_otp(email, otp):
    send_mail(subject="OTP for megadolls sloper account", message=str(otp), from_email=EMAIL_FROM, recipient_list=[email], fail_silently=False)


def mail_send_user_credential(email, password):
    send_mail("Your Sloper Account Credential", str(password), EMAIL_FROM, [email], fail_silently=False)


def send_verification_otp_for_sloper_guest_user(email, otp):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    subject = "OTP To Checkout"
    content = "OTP To Checkout"
    merge_data = {'otp': str(otp), 'content': content, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}  
    html_message = render_to_string("email_html/sloper_emails/sloper-guest-user-checkout-otp.html", merge_data)
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, EMAIL_FROM, [email], fail_silently=False, html_message=html_message)
       
