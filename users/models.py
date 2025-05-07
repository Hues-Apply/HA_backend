from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

import random

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields): 
        if not email:
            raise ValueError('The Email is required.')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    
    username = None
    email = models.CharField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
        
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def generate_otp(self):
        otp = f"{random.randint(100000, 999999)}"
        self.otp = otp
        self.save()
        return otp