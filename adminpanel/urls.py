from unicodedata import name
from django.urls import path
from adminpanel import views
from .views import CategoryView  # , UserManagementView

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # path('register', views.register_user, name='register'),
    path("login", views.login_user, name="login"),
    path("logout", views.logout_user, name="logout"),
    path("forget_password", views.forget_password, name="forget_password"),
    path("change_password", views.change_password, name="change_password"),
    path("profile", views.user_profile, name="profile"),
    path("update_user_profile", views.update_user_profile, name="update_user_profile"),
    path("sidebar_dropdown", views.get_sidebar_dropdown, name="sidebar_dropdown"),
    path("email_template/add", views.add_email_template, name="add_email_template"),
    path(
        "email_template/edit/<id>",
        views.edit_email_template,
        name="edit_email_template",
    ),
    path("email_template/", views.view_email_templates, name="view_email_templates"),
    path("view_message_template", views.view_message_template, name="view_message_template"),
    path("add_message_template", views.add_message_template, name="add_message_template"),
    path("edit_message_template/<int:id>", views.edit_message_template, name="edit_message_template"),
    path("category/add", views.add_category, name="add_category"),
    path("category/update/<id>", views.update_category, name="update_category"),
    path("category/delete", views.delete_category, name="delete_category"),
    path("categories/", views.view_category, name="view_categories"),
    # path('get_categories/', views.get_categories, name="get_categories"),
    path(
        "product_management/shop", views.view_shop_products, name="view_shop_products"
    ),
    path(
        "product_management/shop/add", views.add_shop_product, name="add_shop_product"
    ),
    path(
        "product_management/shop/edit/<int:id>",
        views.edit_shop_product,
        name="edit_shop_product",
    ),
    path(
        "product_management/shop/view/<int:id>",
        views.view_shop_product,
        name="view_shop_product",
    ),
    path(
        "product_management/shop/delete",
        views.delete_shop_product,
        name="delete_shop_product",
    ),
    # path('product_management/shop/delete/<int:id>', views.delete_shop_product, name="delete_shop+
    # _product"),
    path(
        "product_management/shop/delete_shop_product_image",
        views.delete_shop_product_image,
        name="delete_shop_product_image",
    ),
    path(
        "product_management/imagine",
        views.view_imagine_products,
        name="view_imagine_products",
    ),
    path(
        "product_management/imagine/add",
        views.add_imagine_product,
        name="add_imagine_product",
    ),
    path(
        "product_management/imagine/edit/<int:id>",
        views.edit_imagine_product,
        name="edit_imagine_product",
    ),
    path(
        "product_management/imagine/view/<int:id>",
        views.view_imagine_product,
        name="view_imagine_product",
    ),
    path(
        "product_management/imagine/delete",
        views.delete_imagine_product,
        name="delete_imagine_product",
    ),
    path(
        "product_management/imagine/delete_imagine_product_image",
        views.delete_imagine_product_image,
        name="delete_imagine_product_image",
    ),
    path("get_categories/", CategoryView.as_view(), name="get_categories"),
    path("subcategory/add", views.add_subcategory, name="add_subcategory"),
    path(
        "subcategory/update/<int:id>",
        views.update_subcategory,
        name="update_subcategory",
    ),
    path(
        "subcategory/view/<int:id>",
        views.view_subcategory_detail,
        name="view_subcategory_detail",
    ),
    path("subcategory/delete", views.delete_subcategory, name="delete_subcategory"),
    path("subcategories/", views.view_subcategories, name="view_subcategories"),
    path("imagine-subcategories/", views.view_imagine_subcategories, name="view_imagine_subcategories"),
    path("get_sub_categories/", views.get_sub_categories, name="get_sub_categories"),
    path("user_management/add", views.add_user, name="add_user"),
    path("user_management/edit/<user_id>", views.edit_user, name="edit_user"),
    path("user_management/delete", views.delete_user, name="delete_user"),
    path("user_management/", views.view_users, name="view_users"),
    path(
        "user_management/view_user_detail/<user_id>",
        views.view_user_detail,
        name="view_user_detail",
    ),
    path("sub_admin_management/add", views.add_sub_admin, name="add_sub_admin"),
    path(
        "sub_admin_management/edit/<sub_admin_id>",
        views.edit_sub_admin,
        name="edit_sub_admin",
    ),
    path(
        "sub_admin_management/delete", views.delete_sub_admin, name="delete_sub_admin"
    ),
    path("sub_admin_management/", views.view_sub_admins, name="view_sub_admins"),
    path(
        "sub_admin_management/view_sub_admin_detail/<sub_admin_id>",
        views.view_sub_admin_detail,
        name="view_sub_admin_detail",
    ),
    path("super_admin_management/add", views.add_super_admin, name="add_super_admin"),
    path(
        "super_admin_management/edit/<int:id>",
        views.edit_super_admin,
        name="edit_super_admin",
    ),
    path(
        "super_admin_management/delete",
        views.delete_super_admin,
        name="delete_super_admin",
    ),
    path("super_admin_management/", views.view_super_admins, name="view_super_admins"),
    path(
        "super_admin_management/view_super_admin_detail/<int:id>",
        views.view_super_admin_detail,
        name="view_super_admin_detail",
    ),
    path("social_media/add", views.add_social_media, name="add_social_media"),
    path(
        "social_media/edit/<social_media_id>",
        views.edit_social_media,
        name="edit_social_media",
    ),
    path("social_media/delete", views.delete_social_media, name="delete_social_media"),
    path("social_media/", views.view_social_media, name="view_social_media"),
    path("resend_mail/", views.resend_mail, name="resend_mail"),
    path("dress_type/add", views.add_dress_type, name="add_dress_type"),
    path(
        "dress_type/edit/<dress_type_id>", views.edit_dress_type, name="edit_dress_type"
    ),
    path(
        "dress_type/view/<int:id>",
        views.view_dress_type_detail,
        name="view_dress_type_detail",
    ),
    path("dress_type/delete", views.delete_dress_type, name="delete_dress_type"),
    path("dress_type/", views.view_dress_types, name="view_dress_types"),
    path("collection/add", views.add_collection, name="add_collection"),
    path("collection/edit/<int:id>", views.edit_collection, name="edit_collection"),
    path(
        "collection/view/<int:id>",
        views.view_collection_detail,
        name="view_collection_detail",
    ),
    path("collection/delete", views.delete_collection, name="delete_collection"),
    path("collection/", views.view_collections, name="view_collections"),
    path("color/add", views.add_color, name="add_color"),
    path("color/edit/<color_id>", views.edit_color, name="edit_color"),
    path("color/view/<int:id>", views.view_color_detail, name="view_color_detail"),
    path("color/delete", views.delete_color, name="delete_color"),
    path("color/", views.view_colors, name="view_colors"),
    path("blog/add", views.add_blog, name="add_blog"),
    path("blog/edit/<int:id>", views.edit_blog, name="edit_blog"),
    path("blog/delete", views.delete_blog, name="delete_blog"),
    path("blog/", views.view_blogs, name="view_blogs"),
    path(
        "blog_management/view_blog_detail/<int:id>",
        views.view_blog_detail,
        name="view_blog_detail",
    ),
    path("blog_category", views.view_blog_categories, name="view_blog_categories"),
    path("blog_category/add", views.add_blog_category, name="add_blog_category"),
    path(
        "blog_category/edit/<int:id>",
        views.edit_blog_category,
        name="edit_blog_category",
    ),
    path("blog_subcategory/add", views.add_blog_subcategory, name = "add_blog_subcategory"),
    path("blog_subcategory", views.blog_subcategory, name="blog_subcategory"),
    path("edit_subcategory/<int:id>", views.edit_subcategory, name = "edit_subcategory"),
    path("delete_subcategory", views.delete_subcategory, name = "delete_subcategory"),
    path("subcategory_data", views.subcategory_data, name = "subcategory_data"),
    path(
        "blog_categeory/delete", views.delete_blog_category, name="delete_blog_category"
    ),
    path("blog_user/", views.blog_user, name="blog_user"),
    path("delete_blog_user", views.delete_blog_user, name="delete_blog_user"),
    path("view_blog_user/<int:user>", views.view_blog_user, name="view_blog_user"),
    path("edit_blog_user/<int:id>", views.edit_blog_user, name = "edit_blog_user"),
    path(
        "view_blog_user_comment/<int:blog>/<int:user>",
        views.view_blog_user_comment,
        name="view_blog_user_comment",
    ),
    path(
        "delete_blog_user_comment/",
        views.delete_blog_user_comment,
        name="delete_blog_user_comment",
    ),
    path("subscribers", views.subscribers, name = "subscribers"),
    path("delete_comment/", views.delete_comment, name="delete_comment"),
    path("country/add", views.add_country, name="add_country"),
    path("countries/", views.view_countries, name="view_countries"),
    path("country/edit/<int:id>", views.edit_country, name="edit_country"),
    path(
        "country/view/<int:id>", views.view_country_detail, name="view_country_detail"
    ),
    path("country/delete", views.delete_country, name="delete_country"),
    path("view_order_charges", views.view_order_charges, name="view_order_charges"),
    path(
        "edit_order_charge/<int:id>", views.edit_order_charge, name="edit_order_charge"
    ),
    path("contact_us_inquiry", views.contact_us_inquiry, name="contact_us_inquiry"),
    path("resolved_contact_us_inquiry", views.resolved_contact_us_inquiry, name="resolved_contact_us_inquiry"),
    path("view_resolved_inquiry/<int:id>", views.view_resolved_inquiry, name = "view_resolved_inquiry"),
    path("delete_resolved_inquiry", views.delete_resolved_inquiry, name = "delete_resolved_inquiry"),
    path("delete_user_inquiry", views.delete_user_inquiry, name="delete_user_inquiry"),
    path(
        "view_user_inquiry/<int:id>", views.view_user_inquiry, name="view_user_inquiry"
    ),
    path(
        "add_contact_us_details",
        views.add_contact_us_details,
        name="add_contact_us_details",
    ),
    path(
        "add_coordinates_details",
        views.add_coordinates_details,
        name="add_coordinates_details",
    ),
    path("contact_us_details", views.contact_us_details, name="contact_us_details"),
    path("reply_user_inquiry", views.reply_user_inquiry, name="reply_user_inquiry"),
    path(
        "edit_contact_us_details/<int:id>",
        views.edit_contact_us_details,
        name="edit_contact_us_details",
    ),
    path(
        "delete_contact_us_details",
        views.delete_contact_us_details,
        name="delete_contact_us_details",
    ),
    path(
        "default_contact_us_details/<int:id>",
        views.default_contact_us_details,
        name="default_contact_us_details",
    ),
    path("order_management/", views.order_management, name="order_management"),
    path('delete_order_listing', views.delete_order_listing, name="delete_order_listing"),
    path("cancel_order", views.cancel_order, name="cancel_order"),
    path("refund-to-customer/<int:id>/", views.refund_to_customer, name="refund_to_customer"),
    path("view_order/<int:id>/", views.view_order, name = "view_order"),
    path("delete_link_on_blog/", views.delete_link_on_blog, name="delete_link_on_blog"),
    path("view_newsletter/", views.view_newsletter, name="view_newsletter"),
    path("add_newsletter/", views.add_newsletter, name="add_newsletter"),
    path("delete_newsletter/", views.delete_newsletter, name="delete_newsletter"),
    # Guest User 
    path("view-guest-user-order/", views.view_guest_user_order, name = "view_guest_user_order"),
    path("view-guest-user-order-detail/<int:id>/", views.view_guest_user_order_detail, name = "view_guest_user_order_detail"),
    path("delete-guest-user-order/", views.delete_guest_user_order, name = "delete_guest_user_order"),
    # Guest User end
    # ---------------------start Review Management-----------------------------------#
    path("view_reviews/", views.view_reviews, name="view_reviews"),
    path(
        "view_reviews_detail/<int:id>",
        views.view_reviews_detail,
        name="view_reviews_detail",
    ),
    path("edit_reviews/<int:id>", views.edit_reviews, name="edit_reviews"),
    path("delete_reviews/", views.delete_reviews, name="delete_reviews"),
    # ---------------------End Review Management-----------------------------------#
    # ---------------------start Content Management-----------------------------------#
    path("view_terms/", views.view_terms, name="view_terms"),
    path("add_terms/", views.add_terms, name="add_terms"),
    path("edit_terms/<int:id>", views.edit_terms, name="edit_terms"),
    path("view_privacy/", views.view_privacy, name="view_privacy"),
    path("add_privacy/", views.add_privacy, name="add_privacy"),
    path("edit_privacy/<int:id>", views.edit_privacy, name="edit_privacy"),
    path("view_legal/", views.view_legal, name="view_legal"),
    path("add_legal/", views.add_legal, name="add_legal"),
    path("edit_legal/<int:id>", views.edit_legal, name="edit_legal"),
    path("view_shipping/", views.view_shipping, name="view_shipping"),
    path("add_shipping/", views.add_shipping, name="add_shipping"),
    path("edit_shipping/<int:id>", views.edit_shipping, name="edit_shipping"),
    path("view_faq/", views.view_faq, name="view_faq"),
    path("add_faq/", views.add_faq, name="add_faq"),
    path("edit_faq/<int:id>", views.edit_faq, name="edit_faq"),
    path("view_faq_detail/<int:id>", views.view_faq_detail, name="view_faq_detail"),
    path("delete_faq/", views.delete_FAQ, name="delete_faq"),
    # ---------------------End Content Management-----------------------------------#
    # ------------------start- banner management----------------------#
    path("view_slider/", views.view_slider, name="view_slider"),
    path("add_slider/", views.add_slider, name="add_slider"),
    path("edit_slider/<int:id>", views.edit_slider, name="edit_slider"),
    path(
        "view_slider_detail/<int:id>",
        views.view_slider_detail,
        name="view_slider_detail",
    ),
    path("delete_slider/", views.delete_slider, name="delete_slider"),
    path("view_product_shop/", views.view_product_shop, name="view_product_shop"),
    # path("add_product_shop/", views.add_product_shop, name="add_product_shop"),
    path(
        "edit_product_shop/<int:id>", views.edit_product_shop, name="edit_product_shop"
    ),
    path(
        "view_product_shop_detail/<int:id>",
        views.view_product_shop_detail,
        name="view_product_shop_detail",
    ),
    # path("delete_product_shop/", views.delete_product_shop, name="delete_product_shop"),
    path('view_subscription/', views.view_subscription, name="view_subscription"),
    # path('add_subscription/', views.add_subscription, name="add_subscription"),
    path('edit_subscription/<int:id>', views.edit_subscription, name="edit_subscription"),
    # path('delete_subscription/', views.delete_subscription, name="delete_subscription"),
    path('view_detail_subscription/<int:id>', views.view_detail_subscription, name="view_detail_subscription"),

    path('view_product_imagine/', views.view_product_imagine, name="view_product_imagine"),
    # path('add_product_imagine/', views.add_product_imagine, name="add_product_imagine"),
    path('edit_product_imagine/<int:id>', views.edit_product_imagine, name="edit_product_imagine"),
    path('view_product_imagine_detail/<int:id>', views.view_product_imagine_detail, name="view_product_imagine_detail"),
    # path('delete_product_imagine/', views.delete_product_imagine, name="delete_product_imagine"),
    #----------------------End Banner Management-------------------------------------------------------#

    #----------------------start Offer Management------------------------------------------------------#
    path('offer_view/', views.offer_view, name="offer_view"),
    path('offer_add/', views.offer_add, name="offer_add"),
    path('offer_edit/<int:id>', views.offer_edit, name="offer_edit"),
    path('offer_view_detail/<int:id>', views.offer_view_detail, name="offer_view_detail"),
    path('offer_delete/', views.offer_delete, name="offer_delete"),

    #---------------------Gift Card--------------------------------#
    path('giftcard_view/', views.giftcard_view, name="giftcard_view"),
    path('giftcard_add/', views.giftcard_add, name="giftcard_add"),
    path('view_user_gift_card/', views.view_user_gift_card, name="view_user_gift_card"),


    #----------------------Subscription Start----------------------------------------------------------#     
    path('subscription_plan', views.subscription_plan, name="subscription_plan"),
    path('view_subscription_plan/<int:id>', views.view_subscription_plan, name="view_subscription_plan"),
    path('add_subscription_plan', views.add_subscription_plan, name="add_subscription_plan"),
    path('edit_subscription_plan/<int:id>', views.edit_subscription_plan, name="edit_subscription_plan"),
    path('delete_subscription_plan', views.delete_subscription_plan, name="delete_subscription_plan"),
    path('subscription_benefit', views.subscription_benefit, name="subscription_benefit"),
    path('add_subscription_benefit', views.add_subscription_benefit, name="add_subscription_benefit"),
    path('edit_subscription_benefit/<int:id>', views.edit_subscription_benefit, name="edit_subscription_benefit"),
    path('delete_subscription_benefit', views.delete_subscription_benefit, name="delete_subscription_benefit"),
    path('shero_subscribers', views.shero_subscribers, name="shero_subscribers"),
    path("delete_shero_subscribers", views.delete_shero_subscribers, name="delete_shero_subscribers"),
    path("view_subscriber_details/<int:id>", views.view_subscriber_details, name="view_subscriber_details"),

    # ---------------------Shero Dolls Start-----------------------------------------------------------#
    path('shero_dolls', views.shero_dolls, name="shero_dolls"),
    path('add_shero_dolls', views.add_shero_dolls, name="add_shero_dolls"),
    path('edit_shero_dolls/<int:id>', views.edit_shero_dolls, name="edit_shero_dolls"),
    path('view_shero_dolls/<int:id>', views.view_shero_dolls, name="view_shero_dolls"),
    path('delete_shero_dolls', views.delete_shero_dolls, name="delete_shero_dolls"),
    path('delete_shero_dolls_images', views.delete_shero_dolls_images, name="delete_shero_dolls_images"),

    #-----------------------------Gift Card Image------------------------------------#
    path('view_giftcard_image/', views.view_giftcard_image, name="view_giftcard_image"),  
    path('add_giftcard_image/', views.add_giftcard_image, name="add_giftcard_image"),
    path('edit_giftcard_image/<int:id>', views.edit_giftcard_image, name="edit_giftcard_image"),
    path("delete_giftcard_image/", views.delete_giftcard_image, name="delete_giftcard_image"),
    path("giftcard_type", views.giftcard_type, name="giftcard_type"),
    path("add_giftcard_type", views.add_giftcard_type, name="add_giftcard_type"),
    path("edit_giftcard_type/<int:id>", views.edit_giftcard_type, name="edit_giftcard_type"),
    path("delete_giftcard_type", views.delete_giftcard_type, name="delete_giftcard_type"),
    path("delete_giftcard_type_image", views.delete_giftcard_type_image, name="delete_giftcard_type_image"),

    #-----------------------------Referral Start------------------------------------#
    path('referral', views.referral, name="referral"),
    path('view_referral_details/<int:id>', views.view_referral_details, name="view_referral_details"),
    path('delete_referral_user', views.delete_referral_user, name="delete_referral_user"),
    #-----------------------------Links on blog Start------------------------------------#
    path('links_on_blog', views.links_on_blog, name="links_on_blog"),
    path('add_links_on_blog', views.add_links_on_blog, name="add_links_on_blog"),
    path('delete_link_on_blog', views.delete_link_on_blog, name="delete_link_on_blog"),
    path('edit_links_on_blog/<int:id>', views.edit_links_on_blog, name="edit_links_on_blog"),
    path('social_media_link', views.social_media_link, name="social_media_link"),
    path('add_social_media_link', views.add_social_media_link, name="add_social_media_link"),
    path('delete_social_media_link', views.delete_social_media_link, name="delete_social_media_link"),
    path('edit_social_media_link/<int:id>', views.edit_social_media_link, name="edit_social_media_link"),
    #-----------------------------Links on blog End------------------------------------#

    #-----------------------------Sloper Tool Management Start------------------------------------#
    path('sloper_template', views.sloper_template, name="sloper_template"),
    path('add_sloper_template', views.add_sloper_template, name="add_sloper_template"),
    path('view_sloper_template/<int:id>', views.view_sloper_template, name="view_sloper_template"),
    path('edit_sloper_template/<int:id>', views.edit_sloper_template, name="edit_sloper_template"),
    path('delete_sloper_template', views.delete_sloper_template, name="delete_sloper_template"),
    
    path('sloper_texture', views.sloper_texture, name="sloper_texture"),
    path('add_sloper_texture', views.add_sloper_texture, name="add_sloper_texture"),
    path('view_sloper_texture/<int:id>', views.view_sloper_texture, name="view_sloper_texture"),
    path('edit_sloper_texture/<int:id>', views.edit_sloper_texture, name="edit_sloper_texture"),
    path('delete_sloper_texture', views.delete_sloper_texture, name="delete_sloper_texture"),
    
    path('sloper_element', views.sloper_element, name="sloper_element"),
    path('add_sloper_element', views.add_sloper_element, name="add_sloper_element"),
    path('view_sloper_element/<int:id>', views.view_sloper_element, name="view_sloper_element"),
    path('edit_sloper_element/<int:id>', views.edit_sloper_element, name="edit_sloper_element"), 
    path('delete_sloper_element', views.delete_sloper_element, name="delete_sloper_element"), 
    
    path('sloper_multicolor_icon', views.sloper_multicolor_icon, name="sloper_multicolor_icon"),
    path('add_sloper_multicolor_icon', views.add_sloper_multicolor_icon, name="add_sloper_multicolor_icon"),
    path('view_sloper_multicolor_icon/<int:id>', views.view_sloper_multicolor_icon, name="view_sloper_multicolor_icon"),
    path('edit_sloper_multicolor_icon/<int:id>', views.edit_sloper_multicolor_icon, name="edit_sloper_multicolor_icon"), 
    path('delete_sloper_multicolor_icon', views.delete_sloper_multicolor_icon, name="delete_sloper_multicolor_icon"), 
    #-----------------------------Sloper Tool Management End------------------------------------#

    #-----------------------------Notification Start-------------------------------------------#
    path('inquiry_notification', views.inquiry_notification, name="inquiry_notification"),
    path('delete_inquiry_notification/<int:id>', views.delete_inquiry_notification, name="delete_inquiry_notification"),
    path('referral_notification', views.referral_notification, name="referral_notification"),
    path('delete_referral_notification/<int:id>', views.delete_referral_notification, name="delete_referral_notification"),
    path('notification', views.notification, name="notification"),
    path('view_inquiry_notification/<int:id>', views.view_inquiry_notification, name="view_inquiry_notification"),
    path('view_referral_notification/<int:id>', views.view_referral_notification, name="view_referral_notification"),
    path('delete_all_inquiry_notification', views.delete_all_inquiry_notification, name = "delete_all_inquiry_notification"),
    path('delete_all_referral_notification', views.delete_all_referral_notification, name = "delete_all_referral_notification"),
    #-----------------------------Notification End---------------------------------------------#

    #-------------------------------------About Us Start---------------------------------------#
    path("about_us_management", views.about_us_management, name="about_us_management"),  
    #-------------------------------------About Us End-----------------------------------------#
    
    #-------------------------------------Shero Subscription Content-----------------------------------------#
    path("shero_subscription_content", views.shero_subscription_content, name="shero_subscription_content"),
    #-------------------------------------Shero Subscription Content-----------------------------------------#
    

    #-------------------------------------Blog Content-----------------------------------------#
    path("blog_content", views.blog_content, name="blog_content"),
    #-------------------------------------Blog Content-----------------------------------------#


    #-------------------------------------Content Us Content-----------------------------------------#
    path("contact_us_content", views.contact_us_content, name="contact_us_content"),
    #-------------------------------------Content Us Content-----------------------------------------#

    #-------------------------------------Referral Content-----------------------------------------#
    path("referral_content", views.referral_content, name="referral_content"),
    #-------------------------------------Referral Content-----------------------------------------#
    path("view-token-and-key", views.view_token_and_key, name="view_token_and_key"),
    path("edit-token-and-key/<int:token_and_key_id>", views.edit_token_and_key, name="edit_token_and_key"),

    # sloper subscription
    path("sloper-landing-page/edit/banner-img/", views.edit_banner_img, name="edit_banner_img"),
    path("sloper-landing-page/edit/how-it-work/", views.edit_how_it_work, name="edit_how_it_work"),

    path("sloper-landing-page/view/how-it-work-section/", views.view_how_it_work_section, name="view_how_it_work_section"),
    path("sloper-landing-page/add/how-it-work-section/", views.add_how_it_work_section, name="add_how_it_work_section"),
    path("sloper-landing-page/edit/<slug:slug>/how-it-work-section/", views.edit_how_it_work_section, name="edit_how_it_work_section"),
    path("sloper-landing-page/delete/how-it-work-section/", views.delete_how_it_work_section, name="delete_how_it_work_section"),

    path("sloper-landing-page/edit/testimonial/", views.edit_testimonial, name="edit_testimonial"),

    path("sloper-landing-page/view/testimonial-section/", views.view_testimonial_section, name="view_testimonial_section"),
    path("sloper-landing-page/add/testimonial-section/", views.add_testimonial_section, name="add_testimonial_section"),
    path("sloper-landing-page/edit/<slug:slug>/testimonial-section/", views.edit_testimonial_section, name="edit_testimonial_section"),
    path("sloper-landing-page/delete/testimonial-section/", views.delete_testimonial_section, name="delete_testimonial_section"),

    path("sloper-plan-category", views.sloper_plan_category, name='sloper_plan_category'),
    path("add-sloper-plan-category", views.add_sloper_plan_category, name='add_sloper_plan_category'),
    path("edit-sloper-plan-category/<str:slug>/", views.edit_sloper_plan_category, name='edit_sloper_plan_category'),
    path("sloper-plans", views.sloper_plans, name="sloper_plans"),
    path('add-sloper-plan', views.add_sloper_plan, name="add_sloper_plan"),
    path('edit-sloper-plan/<str:slug>/', views.edit_sloper_plan, name="edit_sloper_plan"),
    path('delete-sloper-plan', views.delete_sloper_plan, name="delete_sloper_plan"),
    path('sloper_hospitals', views.sloper_hospitals, name="sloper_hospitals"),
    path('add-sloper-hospital', views.add_sloper_hospital, name="add_sloper_hospital"),
    path('edit-sloper-hospital/<slug:slug>/', views.edit_sloper_hospital, name="edit_sloper_hospital"),
    path('delete-sloper-hospital', views.delete_sloper_hospital, name="delete_sloper_hospital"),
    path('sloper_schools', views.sloper_schools, name="sloper_schools"),
    path('add-sloper-school', views.add_sloper_school, name="add_sloper_school"),
    path('edit-sloper-school/<slug:slug>/', views.edit_sloper_school, name="edit_sloper_school"),
    path('delete-sloper-school', views.delete_sloper_school, name="delete_sloper_school"),    
    # sloper subscription

    # sloper subscriber management start
    path('individual-personal-sloper-subscriber', views.individual_personal_sloper_subscriber , name="individual_personal_sloper_subscriber"),
    path('view-individual-personal-sloper-subscriber/<slug:slug>/', views.view_individual_personal_sloper_subscriber , name="view_individual_personal_sloper_subscriber"),

    path('individual-gift-sloper-subscriber', views.individual_gift_sloper_subscriber , name="individual_gift_sloper_subscriber"),
    path('view-individual-gift-sloper-subscriber/<slug:slug>/', views.view_individual_gift_sloper_subscriber , name="view_individual_gift_sloper_subscriber"),

    path('hospital-sloper-subscriber', views.hospital_sloper_subscriber , name="hospital_sloper_subscriber"),
    path('view-hospital-sloper-subscriber/<slug:slug>/', views.view_hospital_sloper_subscriber , name="view_hospital_sloper_subscriber"),
    # sloper subscriber management end

    # shipping prices start
    path('shipping-prices', views.shipping_prices, name='shipping_prices'),
    path('edit-shipping-price/<slug:slug>/', views.edit_shipping_price, name='edit_shipping_price'),   
    path('add-shipping-price', views.add_shipping_price, name='add_shipping_price'), 
    path('delete-shipping-price', views.delete_shipping_price, name='delete_shipping_price'),
    # shipping prices end
    path('delete-all-selected', views.delete_all_selected, name="delete_all_selected"),

    # Generate report starts
    path('megadolls-<str:subject>-pdf-report', views.generate_pdf, name="generate_pdf"),
    path('megadolls-<str:subject>-csv-report', views.generate_csv, name="generate_csv"),
    # Generate report ends
    path('create_slug_of_shero_product/', views.create_slug_of_shero_product, name="create_slug_of_shero_product"),
    path('create_slug_of_imagine_product/', views.create_slug_of_imagine_product, name="create_slug_of_imagine_product"),
    path('create_user_role', views.create_user_role, name="create_user_role"),
]
