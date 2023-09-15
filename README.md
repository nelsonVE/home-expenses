
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)

# Home expenses project
This is a simple hobby project made to simplify the task of sharing monthly expenses with other
people.

Developed using Django, pyTelegramBot, Bootstrap and HTMX


### More details
This application allows you to:

- [x] Create expenses, select who paid and automatically do shares to each active user in the
project.
- [x] Discount the (active_users_count - 1) / active_users_count part of an amount paid for a
person.
- [x] List all expenses in a specific month and filter by month and year.
- [x] List your expenses in a specific month/year and filter.
- [x] Make automatically a monthly close with the monthly total amount, your discounted amount
and how much you need to pay
- [x] Send an email each 1st of month notifying the payment amount
- [x] Use the telegram bot to request details of the monthly expenses
- [] Allow per user discount and price add
- [] Add permissions (low priority)


## How to setup
To setup the project and run in your machine, please do the follow steps:

1. Clone the github project
```sh
$ git clone https://github.com/nelsonVE/home-expenses.git
$ cd home-expenses
```

2. Create a virtualenv

3. Install all the dependencies using:
```sh
pip install -r requirements.txt
```

4. Declare your environment variables using the `.env.example` file and rename it to `.env`

5. Run the migrations 
```sh
python manage.py migrate
```

6. Run the project 
```sh
python manage.py runserver
```