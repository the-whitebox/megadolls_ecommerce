from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
DOMAIN = settings.SITE_URL

def gift_card_payment(line_item: list=[], success_url: str='', cancel_url: str='', customer_email: str=None):
    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode = 'payment',
        success_url = DOMAIN + success_url,
        cancel_url = DOMAIN + cancel_url,
        line_items=line_item,
        customer_email = customer_email,
        automatic_tax={
            'enabled': True,
        },
)


def create_customer(email:str):
    try:
       return stripe.Customer.create(
            email=email,
        )
    except Exception as e:
        return None
    
    
def create_product(name: str, description: str):
    return stripe.Product.create(name=name, description=description)

def get_product(stripe_product_id: str):
    return stripe.Product.retrieve(stripe_product_id)

def update_product(stripe_product_id: str, name: str, description: str):
    return stripe.Product.modify(
        stripe_product_id,
        name=name,
        description=description
    )

def get_all_product():
    stripe.Product.list()


def delete_product(stripe_product_id: str):
    return stripe.Product.delete(stripe_product_id)

def create_subscription_price(amount: int=0, currency="usd", recurring: dict={"interval": "month", "interval_count": 1}, stripe_product_id: str=''):
    return stripe.Price.create(
        unit_amount=amount,
        currency=currency,
        recurring=recurring,
        product=stripe_product_id,
    )
    
def get_subscription_price(stripe_product_id: str):
    return stripe.Price.retrieve(
        stripe_product_id
    )
    
def update_subscription_price(subscription_price_id: str="", amount: int=0, currency="usd", recurring: dict={"interval": "month", "interval_count": 1}, stripe_product_id: str=''):
    return stripe.Price.modify(
        subscription_price_id,
        unit_amount=amount,
        currency=currency,
        recurring=recurring,
        product=stripe_product_id,
    )

def get_all_subscription_price():
    return stripe.Price.list()


def payment_for_subscription(line_items: list=[], success_url='', cancel_url: str='', user_id: int = None, customer_id: str='', mode='subscription'):
    return stripe.checkout.Session.create(
        client_reference_id = user_id,
        success_url = DOMAIN + success_url,
        cancel_url = DOMAIN + cancel_url,
        payment_method_types= ["card"],
        mode = mode,
        line_items = line_items,
        customer = customer_id,
    )

def retrive_checkout_session(checkout_session_id):
    return stripe.checkout.Session.retrieve(checkout_session_id)

def cancel_stripe_subscription(stripe_subscription_id:str):
    return stripe.Subscription.delete(stripe_subscription_id)

def get_subscription(subscritpion_id:str):
    return stripe.Subscription.retrieve(subscritpion_id)

def create_webhook(url:str='', enabled_events:list=[]):
    return stripe.WebhookEndpoint.create(
        url=url,
        enabled_events=enabled_events,
    )
    
def get_all_web_hooks():
    return stripe.WebhookEndpoint.list()


def create_source(customer_id):
    stripe.Customer.create_source(
        customer_id,
        source="tok_amex",
    )

def create_subscription_schedule(customer_id: str, start_date: int, price_id: str):
    return stripe.SubscriptionSchedule.create(
            customer=customer_id,
            start_date=start_date,
            end_behavior="release",
            phases=[
                {
                    "items": [
                        {
                            "price": price_id,
                            "quantity": 1,
                        },
                    ],
                    "proration_behavior": "none",
                },
            ],
        )

def get_subcription_schedule(id: str):
    return stripe.SubscriptionSchedule.retrieve(id)

def get_payment_intent(payment_intent_id):
    return stripe.PaymentIntent.retrieve(payment_intent_id)

def create_refund(charge_id: str, amount:int):
    return stripe.Refund.create(charge=charge_id, amount=amount)

#  testing
def create_test_clock(frozen_time):
    return stripe.test_helpers.TestClock.create(frozen_time=frozen_time, name="Annual renewal")

def test_create_customer(clock_id):
    return stripe.Customer.create(
        email="jenny.rosen@example.com",
        test_clock=clock_id,
        payment_method="pm_card_visa",
        invoice_settings={"default_payment_method": "pm_card_visa"},
    )

def get_charge_list(customer_id):
    return stripe.Charge.list(customer=customer_id)
