from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import BaseUserManager
import os
import uuid
from django import forms
from django.utils import timezone


def default_uuid():
    return str(uuid.uuid4())

class UserManager(BaseUserManager):
    class Meta:
        app_label = 'motoverse'
    def get_by_natural_key(self, username):
        return self.get(username=username)
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    default_dob = "1985-01-01"
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    m_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    company_phone = models.CharField(max_length=255, blank=True)
    company_email_address = models.CharField(max_length=255, blank=True)
    date_joined = models.TimeField(null=True)
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=255, blank=True)
    billing_state = models.CharField(max_length=255, blank=True)
    billing_zipcode = models.CharField(max_length=255, blank=True)
    billing_country = models.CharField(max_length=255, blank=True)
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=255, blank=True)
    shipping_state = models.CharField(max_length=255, blank=True)
    shipping_zipcode = models.CharField(max_length=255, blank=True)
    shipping_country = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=16, blank=True)
    dateOfBirth = models.DateField(blank=True, null=True, default=default_dob)

    email_verification_code = models.CharField(max_length=6, blank=True)
    email_timestamp = models.DateTimeField(default=timezone.now)  # Set default to current time
    email_verification_tries = models.IntegerField(default=0)
    email_isVerified = models.BooleanField(default=False)
    idType = models.CharField(max_length=20, blank=True)
    idNumber = models.CharField(max_length=50, blank=True)
    mailaddtype = models.CharField(max_length=50, blank=True)
    solidfi = models.CharField(max_length=150, blank=True)
    idv_value = models.CharField(max_length=150, blank=True)
    idv_info_url = models.CharField(max_length=500, blank=True)
    kyc_address= models.CharField(max_length=25, blank=True)
    kyc_dateOfBirth= models.CharField(max_length=25, blank=True)
    kyc_fraud= models.CharField(max_length=25, blank=True)
    kyc_bank = models.CharField(max_length=25, blank=True)
    active_bank_acc_id = models.CharField(max_length=100, blank=True)
    wallet_address = models.CharField(max_length=100, blank=True)
    x_handle = models.CharField(max_length=100, blank=True)
    tg_handle = models.CharField(max_length=100, blank=True)
    ig_handle = models.CharField(max_length=100, blank=True)
    brownie_coin_address = models.CharField(max_length=100, blank=True)


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    objects = UserManager()

class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_id = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50)
    account_label = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.username} - {self.account_id}"

class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=15, primary_key=True)  # Assuming a maximum phone number length of 15 characters (including country code)
    verification_code = models.CharField(max_length=6)  # You can adjust the max_length according to your requirements
    timestamp = models.DateTimeField(auto_now_add=True)
    isVerified = models.BooleanField(default=False)  # Boolean field for verification status
    verification_tries = models.IntegerField(default=0)  # Integer field for verification tries

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = "Phone Verification"
        verbose_name_plural = "Phone Verifications"

class TokenRecord(models.Model):
    contract_address = models.CharField(max_length=255)
    token_id = models.IntegerField()  # Allow zero as a valid value
    token_owner = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token {self.token_id} - {self.token_owner} - {self.created_at}"

class TokenBalance(models.Model):
    contract_address_nft = models.CharField(max_length=255)
    contract_address_erc20 = models.CharField(max_length=255)
    token_owner = models.CharField(max_length=255)
    token_count = models.IntegerField()  # Allow zero as a valid value
    balance = models.DecimalField(max_digits=50, decimal_places=18)  # Increased max_digits to 50
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token {self.contract_address_nft} - {self.token_owner} - {self.token_count} - {self.balance} - {self.created_at}"

class CoinStats(models.Model):
    coin_supply = models.IntegerField()
    blocks_mined = models.IntegerField()
    current_hash_power = models.FloatField()
    mininginfo = models.FloatField(default=0.0)
    #mininginfo = models.CharField(max_length=1000, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CoinStats - Timestamp: {self.timestamp}"

class MagicKey(models.Model):
    tg_id = models.CharField(max_length=255)
    current_block = models.IntegerField()
    magic_key_guess = models.CharField(max_length=1)
    magic_key = models.CharField(max_length=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"CoinStats - Timestamp: {self.timestamp}"
