from django.urls import path
from web_app import views
from .views import *

urlpatterns = [
     path('web_sign_up/', views.web_sign_up, name='web_sign_up'),
     path('make-social-user-verified/', views.make_social_user_verified, name='make_social_user_verified'),
     path('referral_sign_up/<str:slug>/', views.web_sign_up, name='referral_sign_up'),

     path('web_verify_mail/<str:encrptyed_user_id>/', views.web_verify_mail, name='web_verify_mail'),

     path('web_login', views.web_login, name='web_login'),

     path('web_logout', views.web_logout, name='web_logout'),

     path('web_forgot_password', views.web_forgot_password, name='web_forgot_password'),   
     path('resend_otp/<str:jwt_token>', views.resend_otp, name='resend_otp'),       

     path('', views.home, name='home'),

     path('about_us', views.about_us, name='about_us'),

     path('contact_us', views.contact_us, name='contact_us'),
     path("send_referral_email", views.send_referral_email, name= "send_referral_email"),
     
     path('faq', views.faq, name='faq'),

     path('privacy-policy', views.privacy_policy, name='privacy_policy'),

     path('shipping-return-policy', views.shipping_return_policy,
          name='shipping_return_policy'),

     path('term-condition', views.term_condition,
          name='term_condition'),

     path('category_subcategory_dropdown', views.category_subcategory_dropdown,
          name='category_subcategory_dropdown'),
          
     path('imagine/create/', views.create, name='create'),

     path('play_color/<int:id>', views.play_color, name='play_color'),
     path('imagine/play/', views.play, name='play'),
     path('imagine_detail/<slug:slug>/', views.imagine_detail, name='imagine_detail'),
     # path('web_imagine_filter', views.web_imagine_filter, name='web_imagine_filter'),
     path('imagine/<str:subcategory>/<str:slug>/', views.web_imagine_filter, name='web_imagine_filter'),

     path('shop/post-cards/', views.shop_dolls_sets, name='shop_dolls_sets'),
     path('shop/dolls/', views.shop_dolls, name='shop_dolls'),
     path('shop/shero-cards/', views.shop_dress_sets, name='shop_dress_sets'),
     path('shop_doll_detail/<slug>/', views.shop_doll_detail, name='shop_doll_detail'),
     path('web_shop_filter', views.web_shop_filter, name='web_shop_filter'),
     path('collection-according-subcategory-and-product', views.collection_according_subcategory_and_product, name='collection_according_subcategory_and_product'),

     path('view_cart/', views.view_cart, name='view_cart'),
     path('add_to_cart/<slug>/', views.add_to_cart, name='add_to_cart'),
     path('add_shero_to_cart/<slug>/', views.add_shero_to_cart, name="add_shero_to_cart"),
     path('wishlist_add_to_cart/<slug>/', views.wishlist_add_to_cart, name='wishlist_add_to_cart'),
     path('empty_cart', views.empty_cart, name="empty_cart"),
     path('remove_item/<int:product_id>', views.remove_item, name="remove_item"),
     path('remove_shero_dolls/<int:shero_id>', views.remove_shero_dolls, name="remove_shero_dolls"),
     path('decrease_item_count', views.decrease_item_count, name="decrease_item_count"),
     path('increase_item_count', views.increase_item_count, name="increase_item_count"),
     path('user_cart_item_count', views.user_cart_item_count, name="user_cart_item_count"),
     path('anonymous_cart_item_count', views.anonymous_cart_item_count, name='anonymous_cart_item_count'),
     path('cart_sub_total', views.cart_sub_total, name="cart_sub_total"),
     path('get_cart_product_data', views.get_cart_product_data, name="get_cart_product_data"),
     path('apply_offer', views.apply_offer, name='apply_offer'),
     path('remove_offer', views.remove_offer, name='remove_offer'),
     
     path('buy_now/<slug:slug>/', views.buy_now, name="buy_now"),
     path('buy_now_shero_dolls/<slug:slug>/', views.buy_now_shero_dolls, name="buy_now_shero_dolls"),

     path('album_detail', views.album_detail, name='album_detail'),
     path('album', views.album, name='album'),

     path('billing', views.billing, name='billing'),

     path('meaningful-play-detail/<slug:slug>/', views.blog_detail, name='blog_detail'),
     path('edit-meaningful-play_comment/<int:id>', views.edit_blog_comment, name = "edit_blog_comment"),
     path('meaningful-play', views.blog, name='blog'),
     path('meaningful-play-filter-by-subcategory/<int:id>', views.blog_filter_by_subcategory, name = "blog_filter_by_subcategory"),
     path("meaningful-play-subscriber", views.blog_subscriber, name ='blog_subscriber'),
     path("search-in-meaningful-play", views.search_in_blog, name = "search_in_blog"),

     path('delete_blog_comment/', views.delete_blog_comment, name='delete_blog_comment'),

     path('my_account_address', views.my_account_address, name='my_account_address'),
     path('user_address/', UserAddressView.as_view(), name="user_address"),
     path('change_active_address/<int:id>', views.change_active_address, name="change_active_address"),
     path('get_states', views.get_states, name="get_states"),
     path('get_cities', views.get_cities, name="get_cities"),
     path('add_address', views.add_address, name='add_address'),
     # path('edit_address', views.edit_address, name='edit_address'),
     path('delete_address', views.delete_address, name='delete_address'),
     path('edit_address_data', views.edit_address_data, name='edit_address_data'),
     
     path('my_account_favorite', views.my_account_favorite, name='my_account_favorite'),
     path('add_to_favorite_create_detail/<int:id>/', views.add_to_favorite_create_detail, name='add_to_favorite_create_detail'),
     path('remove_to_favorite_create_detail/<int:id>/', views.remove_to_favorite_create_detail, name='remove_to_favorite_create_detail'),
     path('view_favorites', views.view_favorites, name='view_favorites'),
     path('delete_favorite/<int:id>', views.delete_favorite, name='delete_favorite'),
     path('active_favorite_product', views.active_favorite_product, name="active_favorite_product"),

     path('my_account_order_detail/<slug:slug>', views.my_account_order_detail, name='my_account_order_detail'),
     path('my_account_order', views.my_account_order, name='my_account_order'),
     path('cancel_user_order', views.cancel_user_order, name="cancel_user_order"),
     path('my_account_subscription/', views.my_account_subscription, name='my_account_subscription'),
     path('my_account_wallet', views.my_account_wallet, name='my_account_wallet'),
     path('my_account_referrals', views.my_account_referrals, name='my_account_referrals'),

     path('my_account_wishlist', views.my_account_wishlist, name='my_account_wishlist'),
     path('add_to_wishlish_cart/<int:id>', views.add_to_wishlish_cart, name='add_to_wishlish_cart'),
     path('add-to-wishlish-doll-detail/<slug:slug>', views.add_to_wishlish_doll_detail, name='add_to_wishlish_doll_detail'),
     path('remove-from-wishlish-doll-detail/<slug:slug>', views.remove_from_wishlish_doll_detail, name='remove_from_wishlish_doll_detail'),
     path('view_wishlist', views.view_wishlist, name="view_wishlist"),
     path('active_wishlist_product', views.active_wishlist_product, name="active_wishlist_product"),
     path('remove-wishlist-product/<int:product_id>', views.remove_from_wishlist, name="remove_from_wishlist"),

     path('order_confirmation', views.order_confirmation, name='order_confirmation'),

     path('payment', views.payment, name='payment'),

     path('web_profile_edit', views.profile_edit, name='web_profile_edit'),
     path('web_profile', views.profile, name='web_profile'),
     path('mobile_update/<str:country_code>/<str:new_mobile>/', views.mobile_update, name = "mobile_update"),
     path('resend_otp_mobile/<str:country_code>/<str:new_mobile>/', views.resend_otp_mobile, name = "resend_otp_mobile"),

     path('subscription', views.subscription, name='subscription'),
     path('cancel_subscription>', views.cancel_subscription, name="cancel_subscription"),
     path('shero_subscribe/', views.shero_subscribe, name="shero_subscribe"),
     path('buy_shero_dolls/<slug>/', views.buy_shero_dolls, name="buy_shero_dolls"),
     path('success_shero_subscription/', views.success_shero_subscription, name="success_shero_subscription"),
     path('cancel_shero_subscription/', views.cancel_shero_subscription, name="cancel_shero_subscription"),

     path('otp/<str:jwt_token>/', views.otp, name='otp'),
     path('resetpassword/<str:jwt_token>/', views.resetpassword, name='resetpassword'),
     # path('check_existence_anonymous_id', views.check_existence_anonymous_id, name='check_existence_anonymous_id'),

     path('stripe_checkout', views.stripe_checkout, name="stripe_checkout"),
     path('stripe/create-checkout-session', views.create_checkout_session, name="stripe_create_checkout_session"),
     path('success/', views.stripe_success, name="stripe_success"),
     path('cancelled/', views.stripe_cancel, name="stripe_cancel"),
     # path('tax_amount/', views.tax_amount, name="tax_amount"),
     path('shipping_tax/', views.shipping_tax, name="shipping_tax"),
     path('save_order_data_to_session/', views.save_order_data_to_session, name="save_order_data_to_session"),
     path('newsletter', views.newsletter, name='newsletter'),
     path('set_product_rating/', views.set_product_rating, name='set_product_rating'),
     path('load-more-data/', views.load_more_data, name='load-more-data'),
     path('create_gift_card/', views.create_gift_card, name='create_gift_card'),
     path('create-shero-gift-card/', views.create_shero_gift_card, name='create_shero_gift_card'),
     path('success_payment_for_gift_card/', views.success_payment_for_gift_card, name='success_payment_for_gift_card'),
     path('redeem_my_gift_card/', views.redeem_my_gift_card, name='redeem_my_gift_card'),
     path('redeem_otp/', views.redeem_otp, name='redeem_otp'),
     path('gift_card_to_wallet/', views.gift_card_to_wallet, name='gift_card_to_wallet'),
     path('may_like_product_add_cart/<slug>/', views.may_like_product_add_cart, name='may_like_product_add_cart'),
     
     path('may_like_add_to_wishlish_cart/<int:id>', views.may_like_add_to_wishlish_cart, name="may_like_add_to_wishlish_cart"),
     path('stripe_config/', views.stripe_config, name="stripe_config"),
     # path("webhook/", views.stripe_webhook),
     # path('webhook_order_place/', views.webhook_order_place, name='webhook_order_place'),
     path('stripe_webhook/', views.stripe_webhook, name='stripe_webhook'),
     path("social_media_icons", views.social_media_icons, name = "social_media_icons"),
     path("search_product", views.search_product, name = "search_product"),
     
     path("webhook_order_place/",ShipStationWebhook.as_view()),
     path("redeem-shero-subscription", views.redeem_shero_subscription, name="redeem_shero_subscription"),

     # path("testing-creating", views.testing_creating, name = "testing_creating"),
     path("testing", views.testing, name = "testing"),
     path("testing-success/", views.testing_success, name = "testing_success"),

     path("unsubscribe-to-blog/<str:encrptyed_email>/", views.unsubscribe_to_blog, name="unsubscribe_to_blog"),
     path("unsubscribe-to-newsletter/<str:encrptyed_email>/", views.unsubscribe_to_newsletter, name="unsubscribe_to_newsletter"),

     # Guest User
     path("register-guest-user/", views.register_guest_user, name="register_guest_user"),
     path("guest-user-billing/", views.guest_user_billing, name="guest_user_billing"),
     path("add-guest-user-address/", views.add_guest_user_address, name="add_guest_user_address"),
     # path("guest-user-tax-amount/", views.guest_user_tax_amount, name="guest_user_tax_amount"),
     path("guest-user-save-order-data-to-session/", views.guest_user_save_order_data_to_session, name="guest_user_save_order_data_to_session"),
     path("guest-user-payment/", views.guest_user_payment, name="guest_user_payment"),
     path("guest-user-create-checkout-session/", views.guest_user_create_checkout_session, name="guest_user_create_checkout_session"),
     path("guest-user-stripe-success/", views.guest_user_stripe_success, name="guest_user_stripe_success"),
     # Guest User end

     path("download-count-increment/", views.download_count_increment, name="download_count_increment"),
     # Sloper Subscription Start
     path("render-sloper-landing-page/", views.render_sloper_landing_page, name="render_sloper_landing_page"),
     path("summary-sloper-individual-personal-plan", views.summary_sloper_individual_personal_plan, name="summary_sloper_individual_personal_plan"),
     path("pay-school-subscription", views.pay_school_subscription, name="pay_school_subscription"),
     path('checkout-sloper-individual-personal-plan', views.checkout_sloper_individual_personal_plan, name="checkout_sloper_individual_personal_plan"),
     path("checkout-sloper-individual-gift-plan", views.checkout_sloper_individual_gift_plan, name="checkout_sloper_individual_gift_plan"),
     path('summary-sloper-individual-gift-plan', views.summary_sloper_individual_gift_plan, name="summary_sloper_individual_gift_plan"),
     path('stripe-sloper-individual-personal-plan', views.stripe_sloper_individual_personal_plan, name="stripe_sloper_individual_personal_plan"),
     path('stripe-sloper-individual-gift-plan', views.stripe_sloper_individual_gift_plan, name="stripe_sloper_individual_gift_plan"),
     path('add-sloper-personal-plan-type', views.add_sloper_personal_plan_type, name="add_sloper_personal_plan_type"),
     path('add-sloper-gift-plan-type', views.add_sloper_gift_plan_type, name="add_sloper_gift_plan_type"),
     path("add-sloper-personal-billing-address", views.add_sloper_personal_billing_address, name="add_sloper_personal_billing_address"),
     path("add-sloper-gift-billing-address", views.add_sloper_gift_billing_address, name="add_sloper_gift_billing_address"),
     path('sloper-personal-order-confirmation/', views.sloper_personal_order_confirmation, name="sloper_personal_order_confirmation"),
     path('sloper-gift-order-confirmation/', views.sloper_gift_order_confirmation, name="sloper_gift_order_confirmation"),
     path('sloper-personal-order-details/', views.sloper_personal_order_details, name="sloper_personal_order_details"),
     path('sloper-gift-order-details/', views.sloper_gift_order_details, name="sloper_gift_order_details"),
     path("sloper-ckeckout-login", views.sloper_checkout_login, name="sloper_checkout_login"),
     path("sloper-guest-user-checkout-login", views.sloper_guest_user_checkout_login, name="sloper_guest_user_checkout_login"),
     path("verification-otp-for-sloper-guest-user", views.verification_otp_for_sloper_guest_user, name="verification_otp_for_sloper_guest_user"),
     path('save-sloper-hospital-data', views.save_sloper_hospital_data, name='save_sloper_hospital_data'),
     path('summery-sloper-hospital-plan/<str:hospital_name>/<slug:slug>', views.summery_sloper_hospital_plan, name="summery_sloper_hospital_plan"),
     path('summery-sloper-school-plan/<str:school_name>/<slug:slug>', views.summery_sloper_school_plan, name="summery_sloper_school_plan"),
     path('select-hospital-for-sloper-subscription', views.select_hospital_for_sloper_subscription, name="select_hospital_for_sloper_subscription"),
     path('get-search-hospital-data', views.get_search_hospital_data, name="get_search_hospital_data"),
     path('add-plan-type-onetime-or-recurring', views.add_plan_type_onetime_or_recurring, name="add_plan_type_onetime_or_recurring"),
     path('add_school_plan_type_onetime_or_recurring', views.add_school_plan_type_onetime_or_recurring, name='add_school_plan_type_onetime_or_recurring'),
     path('add-hospital-plan-address', views.add_hospital_plan_address, name="add_hospital_plan_address"),
     path('add-school-plan-address', views.add_school_plan_address, name="add_school_plan_address"),
     path("sloper-hospital-order-confirmation/", views.sloper_hospital_order_confirmation, name="sloper_hospital_order_confirmation"),
     path("sloper-hospital-order-details", views.sloper_hospital_order_details, name="sloper_hospital_order_details"),
     path("stripe-webhook-for-schedule-subscription/", views.stripe_webhook_for_schedule_subscription, name="stripe_webhook_for_schedule_subscription"),
     path('activate-sloper-subscription/<slug:slug>/', views.activate_sloper_subscription, name="activate_sloper_subscription"),
     path('cancel-sloper-subscription/<slug:slug>/', views.cancel_sloper_subscription, name='cancel_sloper_subscription'),
     path("select_sloper_school", views.select_sloper_school, name='select_sloper_school'),
     # path('take_model', views.take_model, name='take_model'),
     # path('restore-model/', views.restore_model, name='restore_model'),
     # Sloper Subscription End  
     path('registered-user-reciept/<encrptyed_order_id>/', views.registered_user_reciept, name="registered_user_reciept"),
     path('guest-user-reciept/<encrptyed_order_id>/', views.guest_user_reciept, name="guest_user_reciept"),
     path('rss-feed/', views.rss_feed, name="rss_feed"),
     path('sloper_coming_soon/', views.sloper_coming_soon, name="sloper_coming_soon"),
     path('Start_Fundraising/',views.start_fundraising_page, name="Start_Fundraising"),
]     