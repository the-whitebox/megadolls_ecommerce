import numbers
from twilio.rest import Client
from django.conf import settings
from adminpanel.models import *
from django.utils.html import strip_tags

from_mail=settings.EMAIL_HOST_USER
from_no=settings.TWILIO_NUMBER
sms_sid=settings.TWILIO_ACCOUNT_SID
sms_token=settings.TWILIO_AUTH_TOKEN

# mobile = user mobile number 
# msg = message content

def update_mobile(name, otp, country_code, new_mobile):
    message_data = MessageTemplate.objects.get(title = "Edit Number")
    content = message_data.content
    mobile = f"+{country_code}{new_mobile}"
    html_message = content.format(otp=otp, name=name)
    msg = strip_tags(html_message)
    client = Client(sms_sid,sms_token)
    client.messages.create(body=msg,from_=from_no,to= mobile)                               
                    
def order_confirmation_sms(name,country_code, new_mobile, order_id):
    message_data = MessageTemplate.objects.get(title = "Order Confirmation")
    content = message_data.content
    mobile = f"+{country_code}{new_mobile}"
    html_message = content.format(name= name, order_id=order_id)
    msg = strip_tags(html_message)
    client = Client(sms_sid,sms_token)
    client.messages.create(body=msg,from_=from_no,to= mobile)  

def cancel_order_sms(name,country_code, new_mobile, amount, order_id):
    message_data = MessageTemplate.objects.get(title = "Cancel Order")
    content = message_data.content
    mobile = f"+{country_code}{new_mobile}"
    html_message = content.format(name= name, amount=amount, order_id = order_id)
    msg = strip_tags(html_message)
    client = Client(sms_sid,sms_token)
    client.messages.create(body=msg,from_=from_no,to= mobile)

def shero_subscription_plan_activation(name,country_code, new_mobile):
    message_data = MessageTemplate.objects.get(title = "Shero Subscription Confirmation")
    content = message_data.content
    mobile = f"+{country_code}{new_mobile}"
    html_message = content.format(name= name)
    msg = strip_tags(html_message)
    client = Client(sms_sid,sms_token)
    client.messages.create(body=msg,from_=from_no,to= mobile) 

def cancel_subscription_sms(name,country_code, new_mobile):
    message_data = MessageTemplate.objects.get(title = "Cancel Shero Subscription")
    content = message_data.content
    mobile = f"+{country_code}{new_mobile}"
    html_message = content.format(name= name)
    msg = strip_tags(html_message)
    client = Client(sms_sid,sms_token)
    client.messages.create(body=msg,from_=from_no,to= mobile)  
