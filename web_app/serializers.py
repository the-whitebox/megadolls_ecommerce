from adminpanel.models import *
from rest_framework import serializers
from adminpanel.models import WebState, WebCity

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'


class WebStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebState
        fields = '__all__'


class WebCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebCity
        fields = '__all__'


class WishlistProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'


class FavoriteProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'

class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = '__all__'
