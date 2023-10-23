from django.conf import settings
import taxjar
from .states import get_state

def tax_jar_tax_amount(data):
  try:
    api_key=settings.TAX_JAR_TOKEN
    client = taxjar.Client(api_key=api_key, api_url=taxjar.SANDBOX_API_URL)
    
    line_items = []
    user_address = data.get('user_address')
    product_dict = data.get('product_dict')
    state = get_state(user_address)
      
    i = 1
    for product in data.get('shop_products'):
      discount = 0
      price = product.offer_price if product.offer_price > 0 else product.original_price
      line_items.append({
        'id': str(i),
        'quantity': product_dict.get(product.id),
        'product_tax_code': '20010',
        'unit_price': float(price),
        'discount': discount
      })
      i+=1
    
    order = client.tax_for_order({
      'from_country': 'US',
      'from_state': 'NY',
      'from_city': 'Forest Hills',
      'from_zip': '11375',
      'to_country': user_address.web_country.short_name,
      'to_zip': user_address.zip_code,
      'to_state': state,
      'to_city': user_address.web_city,
      'amount': 15,
      'shipping': data.get('shipping_cost'),
      # 'nexus_addresses': [
      #   {
      #     'country': 'US',
      #     'zip': '11375',
      #     'state': 'NY',
      #   }
      # ],
      'line_items': line_items
    })

    tax_collectable = dict(order).get('amount_to_collect')
    return tax_collectable   
  except taxjar.exceptions.TaxJarConnectionError as err:
      print(err)
  except taxjar.exceptions.TaxJarResponseError as err:
      # 406 Not Acceptable – transaction_id is missing
      print(err.full_response)
  return 0


def guest_user_taxjar_tax_amount(data):
  try:
    api_key=settings.TAX_JAR_TOKEN
    client = taxjar.Client(api_key=api_key, api_url=taxjar.SANDBOX_API_URL)
    
    line_items = []
    address = data.get('address')
    
    i = 1
    for product in data.get('product_detail'):
      line_items.append({
        'id': str(i),
        'quantity': product.get('quantity'),
        'product_tax_code': '20010',
        'unit_price': product.get('price'),
        'discount': 0
      })
      i+=1
    
    
    order = client.tax_for_order({
      'from_country': 'US',
      'from_state': 'NY',
      'from_city': 'Forest Hills',
      'from_zip': '11375',
      'to_country': address.get('country'),
      'to_zip': address.get('zipcode'),
      'to_state': address.get('state'),
      'to_city': address.get('city'),
      'shipping': data.get('shipping_cost'),
      # 'nexus_addresses': [
      #   {
      #     'country': address.get('country'),
      #     'zip': address.get('zipcode'),
      #     'state': address.get('state'),
      #   }
      # ],
      'line_items': line_items
    })

    tax_collectable = dict(order).get('amount_to_collect')
    return tax_collectable
  except taxjar.exceptions.TaxJarConnectionError as err:
      print(err)
  except taxjar.exceptions.TaxJarResponseError as err:
      # 406 Not Acceptable – transaction_id is missing
      print(err.full_response)
  return 0
    