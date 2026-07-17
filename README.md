# DRF6-64 Celery Homework Example

В этом проекте добавлен простой пример интеграции Celery в Django.

## Что реализовано

- `shop_api/celery.py` — конфигурация Celery и расписание через `crontab`
- `shop_api/__init__.py` — импорт Celery-приложения
- `users/tasks.py` — примеры трёх задач:
  - `create_user_audit_log` — запуск через `.delay()`
  - `delete_old_task_files` — периодическая задача через `crontab`
  - `send_registration_email` — SMTP-задача
- `shop_api/settings.py` — настройки брокера и параметров Celery
- `requirements.txt` — добавлены `celery` и `redis`

## Настройка

1. Установите зависимости:
```powershell
pip install -r requirements.txt
```

2. Запустите Redis (или другой брокер):
```powershell
redis-server
```

3. Убедитесь, что переменные окружения заданы (по желанию):
- `CELERY_BROKER_URL` (по умолчанию `redis://127.0.0.1:6379/0`)
- `CELERY_RESULT_BACKEND` (по умолчанию совпадает с брокером)
- `DEFAULT_FROM_EMAIL` (по умолчанию `no-reply@example.com`)

## Запуск

1. Django-сервер:
```powershell
python manage.py runserver
```

2. Celery worker:
```powershell
celery -A shop_api worker --loglevel=info
```

3. Celery beat:
```powershell
celery -A shop_api beat --loglevel=info
```

## Примеры задач

### 1. Задача через `.delay()`
Вызов из кода:
```python
from users.tasks import create_user_audit_log
create_user_audit_log.delay(user.id, 'profile_updated')
```
Эта задача асинхронно обновляет поле `last_login` пользователя.

### 2. Задача по расписанию через `crontab`
`shop_api/celery.py` содержит расписание:
```python
app.conf.beat_schedule = {
    'delete-old-task-files-every-night': {
        'task': 'users.tasks.delete_old_task_files',
        'schedule': crontab(hour=3, minute=0),
    },
}
```
Она удаляет товары без владельца `owner__isnull=True`.

### 3. SMTP-задача
Задача `send_registration_email` отправляет письмо:
```python
from users.tasks import send_registration_email
send_registration_email.delay(user.email, user.first_name)
```
По умолчанию письма выводятся в консоль, если не задан другой `EMAIL_BACKEND`.

## Примечание

Для простого тестирования достаточно запустить Redis, worker и beat. После этого можно вызывать `.delay()` и проверять, что задача выполняется в фоне.
