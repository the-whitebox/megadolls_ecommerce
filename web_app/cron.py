from .email import send_mail_plan_discontinue
from datetime import datetime, timedelta
from adminpanel.models import UserSubscriptions, User
from .payment import cancel_stripe_subscription

def discontinue_shero_subscription_plan():
    current_date = datetime.today() + timedelta(days=1)
    date = current_date.date()
    raw_query = f"""SELECT "adminpanel_usersubscriptions"."id",
	"adminpanel_usersubscriptions"."user_id",
	"adminpanel_usersubscriptions"."shero_subscription_id",
	"adminpanel_usersubscriptions"."customer_id",
	"adminpanel_usersubscriptions"."subscription_id",
	"adminpanel_usersubscriptions"."start_at",
	"adminpanel_usersubscriptions"."expire_at",
	"adminpanel_usersubscriptions"."is_delete"
    FROM "adminpanel_usersubscriptions"
    WHERE "adminpanel_usersubscriptions"."expire_at" = '{date}';"""
    user_subscriptions = UserSubscriptions.objects.raw(raw_query)

    if user_subscriptions:        
        renewed_plan_email = []
        discontinue_plan_email = []

        for shero_subscriber in user_subscriptions:
            if shero_subscriber.shero_subscription.is_active:
                # send mail to notify that your subscription plan is going to renew again
                renewed_plan_email.append(shero_subscriber.user.email)   
            else:
                # cancel shero subscription and notify user by sending mail
                cancel_stripe_subscription(shero_subscriber.subscription_id)
                shero_subscriber.subscription_id = None
                shero_subscriber.start_at = None
                shero_subscriber.expire_at = None
                shero_subscriber.shero_subscription_id = None
                shero_subscriber.save()
                email = shero_subscriber.user.email
                discontinue_plan_email.append(email)
                
        send_mail_plan_discontinue(discontinue_plan_email)

def imagine_download_limit_reset():
    User.object.filter(is_active=True, is_delete=False, is_verified=True, user_type='CUSTOMER').update(download_count=0)