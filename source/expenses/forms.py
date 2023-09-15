from django.utils.translation import gettext_lazy as _
from django.utils.dates import MONTHS
from django.utils import timezone
from django import forms

from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = (
            'category',
            'description',
            'amount',
            'date',
            'paid_by',
        )
        default_attrs = {'class': 'form-control mb-3'}
        select_attrs = {'class': 'form-select mb-3'}
        widgets = {
            'category': forms.Select(attrs={**select_attrs, 'placeholder': _('Category')}),
            'paid_by': forms.Select(attrs={**select_attrs, 'placeholder': _('Paid by')}),
            'description': forms.Textarea(attrs={**default_attrs, 'rows': 3}),
            'date': forms.DateInput(attrs={'type': 'date', 'autocomplete': 'off', **default_attrs}),
            'amount': forms.NumberInput(attrs={'step': '0.01', **default_attrs}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['paid_by'].queryset = self.fields['paid_by'].queryset.filter(is_active=True)
        self.initial['paid_by'] = self.user
        self.initial['date'] = forms.DateInput().format_value(timezone.now())

    def clean_amount(self):
        amount = self.cleaned_data['amount']

        if amount <= 0:
            raise forms.ValidationError(_('Amount should be greater than 0'))

        return amount

    def save(self, commit=True):
        self.instance.created_by = self.user
        return super().save(commit=commit)


class ExpenseFilterForm(forms.Form):
    month = forms.ChoiceField(
        choices=MONTHS.items(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )
    year = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].choices = [(year, year) for year in range(2019, timezone.now().year + 1)]
        self.initial['month'] = timezone.now().month
        self.initial['year'] = timezone.now().year
