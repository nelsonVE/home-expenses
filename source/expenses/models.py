import decimal

from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.conf import settings
from django.db import models

import prettytable as pt


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Expense(models.Model):
    paid_by = models.ForeignKey(
        User,
        verbose_name=_('Paid by'),
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    category = models.ForeignKey(
        Category,
        verbose_name=_('Category'),
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        verbose_name=_('Amount'),
        max_digits=8,
        decimal_places=2
    )
    description = models.TextField(
        verbose_name=_('Description'),
        blank=True,
        null=True
    )
    created_by = models.ForeignKey(
        User,
        verbose_name=_('Created by'),
        on_delete=models.CASCADE
    )
    date = models.DateField(verbose_name=_('Date'))

    def __str__(self) -> str:
        return f'{self.paid_by} - {self.amount}'

    @classmethod
    def get_by_month(cls, year: int, month: int) -> QuerySet['Expense']:
        return Expense.objects.filter(date__year=year, date__month=month)

    @classmethod
    def get_monthly_total(cls, year: int, month: int) -> decimal.Decimal:
        shares = cls.objects.filter(date__year=year, date__month=month)
        total = decimal.Decimal(0.0)

        for share in shares:
            total += share.amount

        return total

    def save(self, **kwargs):
        created = self.pk is None
        super().save(**kwargs)

        if created:
            ExpenseShare.create_from_expense(self)
        else:
            ExpenseShare.update_from_expense(self)


class ExpenseShare(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_shares')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=decimal.Decimal(0.0))

    def __str__(self) -> str:
        return f'{self.user} - {self.amount} - {self.discount} - {self.expense}'

    @staticmethod
    def __get_active_users() -> QuerySet[User]:
        return User.objects.filter(is_active=True)
    
    @classmethod
    def get_by_month(cls, year: int, month: int, user: User) -> QuerySet['ExpenseShare']:
        return ExpenseShare.objects.filter(
            expense__date__year=year,
            expense__date__month=month,
            user=user
        )

    @classmethod
    def create_from_expense(cls, expense: Expense):
        users = cls.__get_active_users()
        shares = []
        total_users = users.count()

        for user in users:
            amount = expense.amount / total_users if user != expense.paid_by else 0.0
            discount = 0.0

            if user == expense.paid_by:
                discount = (expense.amount * (total_users - 1)) / total_users

            share = cls(expense=expense, user=user, amount=amount, discount=discount)
            shares.append(share)

        cls.objects.bulk_create(shares)

    @classmethod
    def update_from_expense(cls, expense: Expense):
        cls.objects.filter(expense=expense).delete()
        cls.create_from_expense(expense)

    @classmethod
    def get_per_user_monthly_total(cls, year: int, month: int) -> decimal.Decimal:
        monthly_total = Expense.get_monthly_total(year, month)
        return monthly_total / cls.__get_active_users().count()

    @classmethod
    def get_monthly_discounted_total(cls, year: int, month: int, user: User) -> decimal.Decimal:
        shares = cls.objects.filter(
            expense__date__year=year,
            expense__date__month=month,
            user=user
        )
        total = decimal.Decimal(0.0)

        for share in shares:
            total += share.discount

        return total

    @classmethod
    def calc_monthly_expense(cls, year: int, month: int):
        users = cls.__get_active_users()
        total_amount = Expense.get_monthly_total(year, month) / users.count()

        shares = cls.objects.filter(
            expense__date__year=year,
            expense__date__month=month
        ).values('user').annotate(
            total_discount=models.Sum('discount')
        )

        # Delete previous month summary
        ExpenseShareSummary.objects.filter(year=year, month=month).delete()

        # Create new summary
        ExpenseShareSummary.objects.bulk_create([
            ExpenseShareSummary(
                user=user,
                year=year,
                month=month,
                total_discount=share['total_discount'],
                total_amount=total_amount,
                to_pay=total_amount - share['total_discount']
            ) for user, share in zip(users, shares)
        ])


class ExpenseShareSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    total_discount = models.DecimalField(max_digits=8, decimal_places=2)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    to_pay = models.DecimalField(max_digits=8, decimal_places=2, default=decimal.Decimal(0.0))
    paid = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.user} ({self.total_amount} - {self.total_discount} = {self.to_pay})'

    def set_paid(self):
        self.paid = True
        self.save(update_fields=['paid'])

    def get_email_body(self) -> str:
        table = pt.PrettyTable()
        table.field_names = [
            _('Date'),
            _('Category'),
            _('Description'),
            _('Total paid'),
            _('Amount'),
            _('Discount'),
            _('To pay'),
        ]

        table.align[_('Total paid')] = 'r'
        table.align[_('Amount')] = 'r'
        table.align[_('Discount')] = 'r'
        table.align[_('To pay')] = 'r'

        table.vrules = pt.ALL
        table.padding_width = 3

        total = Expense.get_monthly_total(self.year, self.month)
        total_per_user = ExpenseShare.get_per_user_monthly_total(self.year, self.month)
        shares = ExpenseShare.objects.filter(
            expense__date__year=self.year,
            expense__date__month=self.month,
            user=self.user
        )

        for share in shares:
            table.add_row([
                share.expense.date,
                share.expense.category,
                share.expense.description,
                round(share.expense.amount),
                round(share.amount),
                round(share.discount),
                round(share.expense.amount - share.discount)
            ])

        table.add_row([
            '',
            '',
            'Total',
            round(total),
            round(total_per_user),
            round(self.total_discount),
            round(self.to_pay)
        ])

        return _("""
            <p>Hi <strong>%s</strong>,</p>
            <p>Here is your monthly expense summary for %s/%s:</p>
            %s
        """) % (
            self.user.username,
            self.month,
            self.year,
            table.get_html_string(attributes={
                'border': '1',
                'style': 'border-width: 1px; border-collapse: collapse;'
            }),
        )

    def get_email_subject(self) -> str:
        return _('Monthly expense summary for %s/%s') % (self.month, self.year)

    def notify_user(self):
        send_mail(
            self.get_email_subject(),
            self.get_email_body(),
            settings.EMAIL_HOST_USER,
            [self.user.email],
            html_message=self.get_email_body(),
            fail_silently=False,
        )
