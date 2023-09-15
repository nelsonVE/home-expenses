import logging

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from django.db.models import QuerySet
from django.utils import timezone

from dateutil.relativedelta import relativedelta

from expenses.models import ExpenseShare, ExpenseShareSummary

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        previous = timezone.now()
        previous_month = previous.month
        previous_year = previous.year

        logger.info('Calculating totals for %s/%s', previous_month, previous_year)

        ExpenseShare.calc_monthly_expense(previous_year, previous_month)

        summaries: QuerySet[ExpenseShareSummary] = ExpenseShareSummary.objects.filter(
            month=previous_month,
            year=previous_year
        )

        [summary.notify_user() for summary in summaries if summary.user.email]

        logger.info('Done')
