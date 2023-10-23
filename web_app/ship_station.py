from .helpers import string_to_list
from adminpanel.models import GuestUserData, ProductOrderData, ShopProduct, UserAddress, WebCountry, UserCart, ProductOrder

from django.conf import settings
import requests, json

headers = {
    "Host": "ssapi.shipstation.com",
    "Authorization": settings.SHIP_STATION_TOKEN,
    "Content-Type": "application/json",
}

def get_carriers():
    url = "https://ssapi.shipstation.com/carriers"
    data = {}
    response = requests.request("GET", url, data=data,headers=headers)
    return response

def shipping_station(request):
    carrier_code = request.POST.get('carrier_code')
    user_id = request.user.id
    address_id = request.POST.get('address_id')
    user_cart = UserCart.objects.get(user_id=user_id)
    total_weight = 0.00
    
    if user_cart.shop_product_list:
        shop_product_list = string_to_list(user_cart.shop_product_list)
        
        shop_products = ShopProduct.objects.filter(id__in=shop_product_list)
        
        for product in shop_products:
            total_weight += float(product.weight)
        
    address = UserAddress.objects.get(id=address_id, user_id=user_id)
    country = WebCountry.objects.get(id=address.web_country_id)
    
    url = "https://ssapi.shipstation.com/shipments/getrates"
    payload = {
        "carrierCode": carrier_code,
        "fromPostalCode": "11375",
        "toCountry": country.short_name,
        "toPostalCode": address.zip_code,
        "weight": 
            {
                "value": total_weight,
                "units": "ounces"
            },
    }
    data = json.dumps(payload)
    response = requests.request("POST", url, data=data, headers=headers)
    return response
        

def guest_user_shipping_station(request, cart_data):
    carrier_code = request.POST.get('carrier_code')
    order_id = request.session['guest_user']['order_id']
    guest_user_data = GuestUserData.objects.filter(order_id=order_id)

    if guest_user_data:
        total_weight = 0
        total_amount = 0
        guest_user_data = guest_user_data.first()
        address = guest_user_data.shipping_address
        if cart_data.shop_product_list:
            shop_product_list = string_to_list(cart_data.shop_product_list)
            shop_products = ShopProduct.objects.filter(id__in=shop_product_list)
            product_data = []
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
                total_weight += float(product.weight)

            guest_user_data.order_detail = product_data
            guest_user_data.total_amount = total_amount
            guest_user_data.save()

        url = "https://ssapi.shipstation.com/shipments/getrates"
        payload = {
            "carrierCode": carrier_code,
            "fromPostalCode": "11375",
            "toCountry": address.get('country'),
            "toPostalCode": address.get('zipcode'),
            "weight": {
                "value": total_weight,
                "units": "ounces"
            },
        }
        data = json.dumps(payload)
        response = requests.request("POST", url, data=data, headers=headers)
        return response
    return None


def create_order(product_order):
    ship_to = product_order.shipping_address
    url = "https://ssapi.shipstation.com/orders/createorder"
    product_order_data = ProductOrderData.objects.filter(product_order_id=product_order.id)
    items = []
    
    for item in product_order_data:
        items.append({
            "sku": item.slug,
            "name": item.shop_product.name,
            "quantity": item.quantity,
            "unitPrice": float(item.per_unit_price),
            "productId": item.shop_product_id
        })
    
    payload = {
        "orderNumber": product_order.order_id,
        "orderDate": str(product_order.order_at),
        "orderStatus": "awaiting_shipment",
        "orderKey": product_order.order_id,
        "customerUsername": product_order.user.email,
        "customerEmail": product_order.user.email,
        "billTo": {
            "name": product_order.user.name,
            "company": None,
            "street1": None,
            "street2": None,
            "street3": None,
            "city": None,
            "state": None,
            "postalCode": None,
            "country": None,
            "phone": None,
            "residential": None
        },
        "shipTo": {
            "name": product_order.user.name,
            "company": None,
            "street1": f'{ship_to.area_name}',
            "street2": None,
            "street3": None,
            "city": ship_to.web_city,
            "state": ship_to.web_state.name,
            "postalCode": ship_to.zip_code,
            "country": ship_to.web_country.short_name,
            "phone": ship_to.phone,
            "residential": True
        },
        "items": items,
        "amountPaid": float(product_order.total_amount),
        "taxAmount": float(product_order.tax),
        "shippingAmount": float(product_order.shipping_charge),
        "tagIds": []
    }
    data = json.dumps(payload)
    response = requests.request("POST", url, headers=headers, data = data)


def guest_user_create_order(guest_user_data):
    ship_to = guest_user_data.shipping_address
    url = "https://ssapi.shipstation.com/orders/createorder"
    items = []

    shipping_charge = float(guest_user_data.shipping_charge)
    tax = float(guest_user_data.tax)
    total = round(float(guest_user_data.total_amount) + shipping_charge + tax, 2)
    
    for item in guest_user_data.order_detail:
        items.append({
            "sku": item.order_id,
            "name": item.get('name', None),
            "quantity": item.get('quantity'),
            "unitPrice": float(item.get('price')),
            "productId": item.get('id')
        })
    
    payload = {
        "orderNumber": guest_user_data.order_id,
        "orderDate": str(guest_user_data.order_at),
        "orderStatus": "awaiting_shipment",
        "orderKey": guest_user_data.order_id,
        "customerUsername": guest_user_data.email,
        "customerEmail": guest_user_data.email,
        "billTo": {
            "name": ship_to.get('name'),
            "company": None,
            "street1": f"{ship_to.get('area_name')}",
            "street2": None,
            "street3": None,
            "city": ship_to.get('city'),
            "state": ship_to.get('state'),
            "postalCode": ship_to.get('zipcode'),
            "country": ship_to.get('country'),
            "phone": ship_to.get('phone'),
            "residential": True
        },
        "shipTo": {
            "name": ship_to.get('name'),
            "company": None,
            "street1": f"{ship_to.get('area_name')}",
            "street2": None,
            "street3": None,
            "city": ship_to.get('city'),
            "state": ship_to.get('state'),
            "postalCode": ship_to.get('zipcode'),
            "country": ship_to.get('country'),
            "phone": ship_to.get('phone'),
            "residential": True
        },
        "items": items,
        "amountPaid": float(total),
        "taxAmount": float(tax),
        "shippingAmount": float(shipping_charge),
        "tagIds": []
    }
    data = json.dumps(payload)
    response = requests.request("POST", url, headers=headers, data = data)

def delete_order(order_id):
    url = 'https://ssapi.shipstation.com/orders/createorder'
    product_order = ProductOrder.objects.get(order_id=order_id)
    ship_to = product_order.shipping_address

    payload = {
        "orderNumber": order_id,
        "orderDate": str(product_order.order_at),
        "orderStatus": "cancelled",
        "orderKey": order_id,
        "customerUsername": product_order.user.email,
        "customerEmail": product_order.user.email,
        "billTo": {
            "name": product_order.user.name,
            "company": None,
            "street1": None,
            "street2": None,
            "street3": None,
            "city": None,
            "state": None,
            "postalCode": None,
            "country": None,
            "phone": None,
            "residential": None
        },
        "shipTo": {
            "name": product_order.user.name,
            "company": None,
            "street1": f'{ship_to.area_name}',
            "street2": None,
            "street3": None,
            "city": ship_to.web_city,
            "state": ship_to.web_state.name,
            "postalCode": ship_to.zip_code,
            "country": ship_to.web_country.short_name,
            "phone": ship_to.phone,
            "residential": True
        },
        "amountPaid": float(product_order.total_amount),
        "taxAmount": float(product_order.tax),
        "shippingAmount": float(product_order.shipping_charge),
        "tagIds": []
    }

    response = requests.request("POST", url, headers=headers, json=payload)
    # print(response.status_code, response.text.encode('utf8'), "heloooooooooooooooooooooooooooooooooooooooooo")