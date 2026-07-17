from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.managers import CustomUserManager    
from django.core.exceptions import ValidationError


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    birthdate = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    registration_source = models.CharField(max_length=20, default="local")
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    REQUIRED_FIELDS = []
    USERNAME_FIELD = "email"

    def clean(self):
        super().clean()
        if self.is_superuser and not self.phone_number:
            raise ValidationError("Суперпользователь обязан указать номер телефона")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email or ""