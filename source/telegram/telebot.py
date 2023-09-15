from decimal import getcontext

from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.conf import settings

import prettytable as pt
import telebot

from expenses.models import ExpenseShare
from .models import TelegramUser

bot = telebot.TeleBot(settings.TELEBOT_API_TOKEN, threaded=False)


@bot.message_handler(commands=['registrar'])
def register_user(message):
    username = message.text
    username = username.replace('/registrar ', '')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        bot.reply_to(message, _('User does not exist'))
        return

    TelegramUser.objects.create(user=user, telegram_id=message.chat.id)
    bot.reply_to(message, _('User registered'))


@bot.message_handler(commands=['gastos'])
def user_expenses(message):
    chat_id = message.chat.id

    try:
        telegram_user = TelegramUser.objects.get(telegram_id=chat_id)
    except TelegramUser.DoesNotExist:
        bot.reply_to(message, _('User not registered'))
        return

    user = telegram_user.user
    msg = message.text.replace('/gastos ', '')

    try:
        month, year = msg.split(' ')
    except ValueError:
        bot.reply_to(message, _('Invalid date'))
        return

    expenses_shares: QuerySet[ExpenseShare] = user.expense_shares.all() # type: ignore

    if not expenses_shares:
        bot.reply_to(message, _('No expenses registered'))
        return

    table = pt.PrettyTable(['Category', 'Amount'])
    table.padding_width = 1
    table.align['Category'] = 'l'
    table.align['Amount'] = 'r'

    for expense_share in expenses_shares:
        table.add_row([expense_share.expense.category.name, expense_share.amount])
    

    per_user = ExpenseShare.get_per_user_monthly_total(year, month)
    user_discounts = ExpenseShare.get_monthly_discounted_total(year, month, user)
    text = f'```{table.get_string()}```\n\n'
    text += _('Subtotal: %s\n') % round(per_user, 2)
    text += _('Discounts: %s\n') % round(user_discounts, 2)
    text += _('Total: %s\n') % round(per_user - user_discounts, 2)
    bot.send_message(chat_id, text, parse_mode='Markdown')


def send_message(user: User, message: str):
    try:
        telegram_user = TelegramUser.objects.get(user=user)
    except TelegramUser.DoesNotExist:
        return

    bot.send_message(telegram_user.telegram_id, message)


bot.infinity_polling()