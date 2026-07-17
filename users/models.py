from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.managers import CustomUserManager    
from django.core.exceptions import ValidationError


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, default="")
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


class ConfirmationCode(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='confirmation_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Код подтверждения для {self.user.email}"