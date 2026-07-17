from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import ConfirmationCode, CustomUser


class UserBaseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AuthValidateSerializer(UserBaseSerializer):
    pass


class RegisterValidateSerializer(UserBaseSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True, default='', write_only=True)
    birthdate = serializers.DateField(required=False, allow_null=True, write_only=True)

    def validate_email(self, email):
        email = email.lower()
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('User уже существует!')
        return email

    def validate_phone_number(self, value):
        return value.strip() if value else ''


class ConfirmationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        code = attrs.get('code')

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise ValidationError('User не существует!')

        try:
            confirmation_code = ConfirmationCode.objects.get(user=user)
        except ConfirmationCode.DoesNotExist:
            raise ValidationError('Код подтверждения не найден!')

        if confirmation_code.code != code:
            raise ValidationError('Неверный код подтверждения!')

        return attrs