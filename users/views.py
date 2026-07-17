from django.db import transaction
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
    ConfirmationSerializer
)
from .models import ConfirmationCode, CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
import random
import string


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


class AuthorizationAPIView(CreateAPIView):
    serializer_class = AuthValidateSerializer

    @swagger_auto_schema(request_body=AuthValidateSerializer)
    def post(self, request, *args, **kwargs):
        serializer = AuthValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_serializer = CustomTokenObtainPairSerializer(data=request.data)
        token_serializer.is_valid(raise_exception=True)
        return Response(token_serializer.validated_data)


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

            # Create a random 6-digit code
            code = ''.join(random.choices(string.digits, k=6))

            confirmation_code = ConfirmationCode.objects.create(
                user=user,
                code=code
            )

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

            refresh = RefreshToken.for_user(user)
            if user.birthdate:
                refresh['birthdate'] = user.birthdate.isoformat()
                refresh.access_token['birthdate'] = user.birthdate.isoformat()

            ConfirmationCode.objects.filter(user=user).delete()

        return Response(
            status=status.HTTP_200_OK,
            data={
                'message': 'User аккаунт успешно активирован',
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        )