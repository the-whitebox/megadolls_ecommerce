from django.db import models

class ShopProduct(models.Model):
    # ... Other fields ...

    # Referral code associated with the product
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # Referral commission rate (e.g., 20%)
    referral_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.20)