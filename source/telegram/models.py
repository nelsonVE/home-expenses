from django.contrib.auth.models import User
from django.db import models


class TelegramUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='telegram_user')
    telegram_id = models.IntegerField(unique=True)

    def __str__(self) -> str:
        return f'{self.user} - {self.telegram_id}'
