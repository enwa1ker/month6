from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import CustomUser

@shared_task
def create_user_audit_log(user_id, action):
    CustomUser.objects.filter(id=user_id).update(last_login=timezone.now())

@shared_task
def delete_old_task_files():
    from product.models import Product
    Product.objects.filter(owner__isnull=True).delete()

@shared_task
def send_registration_email(email, username):
    subject = 'Добро пожаловать в проект'
    message = f'Привет, {username}! Спасибо за регистрацию.'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
