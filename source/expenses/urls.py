
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


urlpatterns = [
    path('', login_required(views.HomeView.as_view()), name='home'),
    path('expense/', login_required(views.ExpenseFormView.as_view()), name='expense'),
    path('expense/list/', login_required(views.ExpenseListView.as_view()), name='expense-list'),
    path('expense/list/user/', login_required(views.ExpenseShareListView.as_view(is_user=True)), name='expense-user-list'),
]
