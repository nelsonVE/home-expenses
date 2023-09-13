from django.contrib import admin
from .models import Category, Expense, ExpenseShare


class ExpenseShareInline(admin.TabularInline):
    model = ExpenseShare
    extra = 0


class ExpenseAdmin(admin.ModelAdmin):
    inlines = [ExpenseShareInline]


admin.site.register(Category)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseShare)