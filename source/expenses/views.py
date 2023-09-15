from datetime import datetime

from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.contrib import messages
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from django.views import View

from .forms import ExpenseForm, ExpenseFilterForm
from .models import Expense, ExpenseShare
from .mixins import FilterMixin


class HomeView(View):
    def get_context_data(self, **kwargs):
        queryset = Expense.objects.filter(
            date__year=timezone.now().year
        ).values(
            "date__month"
        ).annotate(
            total=Sum("amount")
        ).order_by(
            "date__month"
        )
        context = {}
        context["expenses"] = {
            datetime(1900, month["date__month"], 1).strftime("%B"): month["total"]
            for month in queryset
        }
        return context
    
    def get(self, request):
        return render(request, 'home.html', self.get_context_data())


class ExpenseFormView(FormView):
    form_class = ExpenseForm
    template_name = 'expense_form.html'

    def get_success_url(self):
        return self.request.path

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, _('Error while creating expense'))
        return super().form_invalid(form)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Expense created successfully'))
        return super().form_valid(form)


class ExpenseListView(View, FilterMixin):

    def get_context_data(self) -> dict:
        month = self.get_month(self.request)
        year = self.get_year(self.request)

        context = {}
        context['expenses'] = Expense.get_by_month(year, month)
        context['total'] = Expense.get_monthly_total(year, month)
        context['month_name'] = timezone.datetime(year, month, 1).strftime('%B')
        context['year_number'] = year
        context['filter_form'] = ExpenseFilterForm(initial={'month': month, 'year': year})

        return context

    def get(self, request):
        return render(request, 'expense_list.html', self.get_context_data())


class ExpenseShareListView(View, FilterMixin):
    def get_context_data(self) -> dict:
        month = self.get_month(self.request)
        year = self.get_year(self.request)

        context = {}
        context['expenses'] = ExpenseShare.get_by_month(
            year,
            month,
            user=self.request.user  # type: ignore
        )
        context['total_per_user'] = ExpenseShare.get_per_user_monthly_total(year, month)
        context['total_to_discount'] = ExpenseShare.get_monthly_discounted_total(
            year,
            month,
            user=self.request.user  # type: ignore
        )
        context['total'] = context['total_per_user'] - context['total_to_discount']
        context['month_name'] = timezone.datetime(year, month, 1).strftime('%B')
        context['year_number'] = year
        context['filter_form'] = ExpenseFilterForm(initial={'month': month, 'year': year})

        return context

    def get(self, request):
        return render(request, 'expense_share.html', self.get_context_data())
