from django.conf import settings
from django.core.mail import send_mail
from .models import User, EmailTemplate
from django.core.mail import EmailMessage
from threading import Thread
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.html import format_html


EMAIL_FROM = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD

class EmailThread(Thread):
    def __init__(self, subject, html_message, recipient_list):
        self.subject = subject
        self.html_messages = html_message
        self.recipient_list = recipient_list
        Thread.__init__(self)

    def run (self):
        msg = EmailMessage(subject = self.subject, body = self.html_messages, from_email = EMAIL_FROM, bcc = self.recipient_list)
        msg.content_subtype = "html"
        msg.send()


def superadmin_create_mail(email, password, name):
    recipient_list = [email]
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}adminpanel'
    email_data = EmailTemplate.objects.get(title = "New Blog")
    subject = "Megadolls Superadmin Created"
    content = email_data.content
    merge_data = {'content': content, 'name': name, 'password': password, 'email': email, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/superadmin-created.html", merge_data)
    EmailThread(subject=subject, html_message=html_message, recipient_list=recipient_list).start()

          

# to send mail to all blog subscribers when new blog is created
def new_blog_post(recipient_list, heading):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    email_data = EmailTemplate.objects.get(title = "New Blog")
    subject = email_data.subject
    content = email_data.content
    merge_data = {'content': content, 'heading': heading, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/the-blog-article.html", merge_data)
    EmailThread(subject=subject, html_message=html_message, recipient_list=recipient_list).start()

# to send mail to all newsletter subscribers when admin sends mail
def newsletter_mail_to_subscribers(recipient_list, subject, content_html):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    content = strip_tags(content_html)
    v = format_html(content)
    merge_data = {'content': v, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/newsletter.html", merge_data)
    EmailThread(subject=subject, html_message=html_message, recipient_list=recipient_list).start()


# to send mail to users when admin replys to user's inquiry
def reply_to_user_inquiry(email, reply_text):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    subject = "Reply to your Inquiry"
    content = strip_tags(reply_text)
    merge_data = {'content': content, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string('email_template/reply_to_inquiry.html', merge_data)
    EmailThread(subject=subject, html_message=html_message, recipient_list=recipient_list).start()


# to send mail to subadmin when subadmin is created 
def add_sub_admin_mail(email, username, password):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    email_data = EmailTemplate.objects.get(title = "Add Sub Admin Mail")
    content = email_data.content
    merge_data = {'content': content, 'email': email, 'username': username, 'password': password, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/add-sub-admin.html", merge_data)
    EmailThread(subject=email_data.subject, html_message=html_message, recipient_list=recipient_list).start()


# to send mail to subadmin to reset password when aubadmin click on forgot password
def forgot_password(email, password):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    email_data = EmailTemplate.objects.get(title = "Superadmin Forgot Password")
    content = email_data.content
    merge_data = {'content': content, 'password': password, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/superadmin-forgot-password.html", merge_data)
    EmailThread(subject=email_data.subject, html_message=html_message, recipient_list=recipient_list).start()


# to send mail to user when admin changes user's password
def admin_changed_user_password_mail(email, name, password):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    email_data = EmailTemplate.objects.get(title = "Admin Changed User Password")
    content = email_data.content
    merge_data = {'name': name, 'content': content, 'password': password, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/admin-changed-user-password.html", merge_data)
    EmailThread(subject=email_data.subject, html_message=html_message, recipient_list=recipient_list).start()
 

# to send mail to customer when order is canceled by admin
def admin_canceled_order_mail(name, email, order_id, time):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    email_data = EmailTemplate.objects.get(title = "Admin Canceled User Order")
    content = email_data.content
    merge_data = {'name': name, 'content': content, 'order_id': order_id, 'time': time, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/admin-canceled-user-order.html", merge_data)
    EmailThread(subject=email_data.subject, html_message=html_message, recipient_list=recipient_list).start()


# to send mail to customer when admin refund the amount to wallet
def admin_refund_amount_to_wallet_order_mail(email, order_id, time):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    email_data = EmailTemplate.objects.get(title = "Amount Refunded For Cancelling Order")
    content = email_data.content
    merge_data = {'content': content, 'order_id': order_id, 'time': time, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/amount-refunded.html", merge_data)
    EmailThread(subject=email_data.subject, html_message=html_message, recipient_list=recipient_list).start()
    

# to send mail to when admin user's added mail
def admin_added_user_mail(name, email, password):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    email_data = EmailTemplate.objects.get(title = "Admin Added User Mail")
    content = email_data.content
    merge_data = {'content': content, 'password': password, 'name': name, 'email': email, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/admin-added-user.html", merge_data)
    EmailThread(subject=email_data.subject, html_message=html_message, recipient_list=recipient_list).start()
   
def mail_to_hospital_on_add(name, email, password=None):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    content = "Hospital registered on Megadolls.com"
    merge_data = {'content': content, 'password': password, 'name': name, 'email': email, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/admin-added-user.html", merge_data)
    EmailThread(subject="Hospital Registered on Megadolls.com", html_message=html_message, recipient_list=recipient_list).start()

def mail_to_school_on_add(name, email, password=None):
    explore_link = settings.SITE_URL
    learn_more_link = f'{settings.SITE_URL}about_us'
    login_signup_link = f'{settings.SITE_URL}web_login'
    recipient_list = [email]
    content = "School registered on Megadolls.com"
    merge_data = {'content': content, 'password': password, 'name': name, 'email': email, 'explore_link': explore_link, 'learn_more_link': learn_more_link, 'login_signup_link': login_signup_link}
    html_message = render_to_string("email_template/admin-added-user.html", merge_data)
    EmailThread(subject="School Registered on Megadolls.com", html_message=html_message, recipient_list=recipient_list).start()
