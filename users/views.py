import json
import os
import urllib.error
import urllib.request

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.generics import CreateAPIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer,
    GoogleAuthSerializer
)
from .models import CustomUser
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
import random
import string

GOOGLE_TOKEN_INFO_URL = 'https://oauth2.googleapis.com/tokeninfo?id_token={}'


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        if user.birthdate:
            token['birthdate'] = user.birthdate.isoformat()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise ValidationError('User account is not activated yet!')
        if self.user.birthdate:
            data['birthdate'] = self.user.birthdate.isoformat()
        return data


def verify_google_id_token(id_token):
    if not id_token:
        raise ValidationError('id_token is required')

    try:
        with urllib.request.urlopen(GOOGLE_TOKEN_INFO_URL.format(id_token), timeout=10) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError:
        raise ValidationError('Invalid Google token')
    except Exception:
        raise ValidationError('Could not verify Google token')

    if settings.GOOGLE_CLIENT_ID:
        if data.get('aud') != settings.GOOGLE_CLIENT_ID:
            raise ValidationError('Google token audience mismatch')

    issuer = data.get('iss')
    if issuer not in ['accounts.google.com', 'https://accounts.google.com']:
        raise ValidationError('Invalid Google token issuer')

    if data.get('email_verified') not in ['true', 'True', '1']:
        raise ValidationError('Google email is not verified')

    return data


class AuthorizationAPIView(CreateAPIView):
    serializer_class = AuthValidateSerializer

    @swagger_auto_schema(request_body=AuthValidateSerializer)
    def post(self, request, *args, **kwargs):
        serializer = AuthValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_serializer = CustomTokenObtainPairSerializer(data=request.data)
        token_serializer.is_valid(raise_exception=True)
        return Response(token_serializer.validated_data)


class GoogleLoginAPIView(CreateAPIView):
    serializer_class = GoogleAuthSerializer

    @swagger_auto_schema(request_body=GoogleAuthSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_data = verify_google_id_token(serializer.validated_data['id_token'])
        email = token_data.get('email')
        if not email:
            raise ValidationError('Google token does not contain email')

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': token_data.get('given_name', ''),
                'last_name': token_data.get('family_name', ''),
                'is_active': True,
                'registration_source': 'google'
            }
        )

        if not created:
            user.first_name = token_data.get('given_name', user.first_name)
            user.last_name = token_data.get('family_name', user.last_name)
            user.registration_source = 'google'
            user.is_active = True

        user.last_login = timezone.now()
        user.save()

        refresh = RefreshToken.for_user(user)
        if user.birthdate:
            refresh['birthdate'] = user.birthdate.isoformat()
            refresh.access_token['birthdate'] = user.birthdate.isoformat()

        return Response(
            status=status.HTTP_200_OK,
            data={
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'registration_source': user.registration_source,
            }
        )


class RegistrationAPIView(CreateAPIView):
    serializer_class = RegisterValidateSerializer

    @swagger_auto_schema(request_body=RegisterValidateSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        phone_number = serializer.validated_data.get('phone_number', '')
        birthdate = serializer.validated_data.get('birthdate')

        # Use transaction to ensure data consistency
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                phone_number=phone_number,
                birthdate=birthdate,
                is_active=False
            )

            # Create a random 6-digit code and store it in Redis for 5 minutes
            code = ''.join(random.choices(string.digits, k=6))
            cache_key = f'confirmation_code:{user.id}'
            cache.set(cache_key, code, timeout=300)

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'user_id': user.id,
                'confirmation_code': code
            }
        )


class ConfirmUserAPIView(CreateAPIView):
    serializer_class = ConfirmationSerializer

    @swagger_auto_schema(request_body=ConfirmationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']

        with transaction.atomic():
            user = CustomUser.objects.get(id=user_id)
            user.is_active = True
            user.save()

            cache.delete(f'confirmation_code:{user.id}')

            refresh = RefreshToken.for_user(user)
            if user.birthdate:
                refresh['birthdate'] = user.birthdate.isoformat()
                refresh.access_token['birthdate'] = user.birthdate.isoformat()

        return Response(
            status=status.HTTP_200_OK,
            data={
                'message': 'User аккаунт успешно активирован',
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        )