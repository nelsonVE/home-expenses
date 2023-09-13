import decimal

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db import models



class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Expense(models.Model):
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
