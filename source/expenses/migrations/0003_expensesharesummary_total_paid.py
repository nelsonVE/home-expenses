# Generated by Django 4.2.5 on 2023-09-13 11:37

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0002_expensesharesummary'),
    ]

    operations = [
        migrations.AddField(
            model_name='expensesharesummary',
            name='total_paid',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=8),
        ),
    ]
