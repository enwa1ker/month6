from datetime import date
from rest_framework.exceptions import ValidationError


def validate_user_age_from_token(token):
    if not token:
        raise ValidationError('Укажите дату рождения, чтобы создать продукт.')

    birthdate = token.payload.get('birthdate') if hasattr(token, 'payload') else None
    if not birthdate:
        raise ValidationError('Укажите дату рождения, чтобы создать продукт.')

    try:
        birthdate_date = date.fromisoformat(birthdate)
    except ValueError:
        raise ValidationError('Укажите дату рождения, чтобы создать продукт.')

    today = date.today()
    age = today.year - birthdate_date.year - ((today.month, today.day) < (birthdate_date.month, birthdate_date.day))
    if age < 18:
        raise ValidationError('Вам должно быть 18 лет, чтобы создать продукт.')
