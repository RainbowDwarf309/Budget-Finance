""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import re
from typing import List, NamedTuple, Optional

import pytz

import db
import exceptions
from categories import Categories


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: int
    category_text: str


class Expense(NamedTuple):
    """Структура добавленного в БД нового расхода"""
    id: Optional[int]
    amount: int
    category_name: str


def add_expense(raw_message: str) -> Expense:
    """Добавляет новое сообщение.
    Принимает на вход текст сообщения, пришедшего в бот."""
    parsed_message = _parse_message(raw_message)
    category = Categories().get_category(
        parsed_message.category_text)
    db.insert("expense", {
        "amount": parsed_message.amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": raw_message
    })
    return Expense(id=None,
                   amount=parsed_message.amount,
                   category_name=category.name)


def get_today_statistics() -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()
    cursor.execute("select sum(amount)"
                   "from expense where date(created)=date('now', 'localtime')")
    result = cursor.fetchone()
    if not result[0]:
        return "Сегодня ещё нет расходов"
    all_today_expenses = result[0]
    result = _get_summary_amount_today_expenses(True)
    base_today_expenses = result[0] if result[0] else 0
    result = _get_summary_amount_today_expenses(False)
    minor_expenses = result[0] if result[0] else 0
    apartment_expenses = _get_apartment_expenses(first_day_of_month)
    return (f"Расходы сегодня:\n"
            f"всего — {all_today_expenses} руб.\n"
            f"квартира — {apartment_expenses} руб. из {_get_apartment_limit()} руб.\n"
            f"второстепенные — {minor_expenses} руб. \n"
            f"базовые — {base_today_expenses} руб. из {_get_budget_limit()} руб.\n\n"
            f"За текущий месяц: /month\n"
            f"За текущий год: /year")


def get_month_statistics() -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}'")
    result = cursor.fetchone()
    if not result[0]:
        return "В этом месяце ещё нет расходов"
    all_today_expenses = result[0]
    result = _get_summary_amount_expenses(first_day_of_month, True)
    base_today_expenses = result[0] if result[0] else 0
    result = _get_summary_amount_expenses(first_day_of_month, False)
    minor_expenses = result[0] if result[0] else 0
    apartment_expenses = _get_apartment_expenses(first_day_of_month)
    return (f"Расходы в текущем месяце:\n"
            f"всего — {all_today_expenses} руб.\n"
            f"квартира — {apartment_expenses} руб. из {_get_apartment_limit()} руб.\n"
            f"второстепенные — {minor_expenses} руб. \n"
            f"базовые — {base_today_expenses} руб. из "
            f"{now.day * _get_budget_limit() + _get_apartment_limit()} руб.")


def get_year_statistics() -> str:
    """Возвращает строкой статистику расходов за текущий год"""
    now = _get_now_datetime()
    first_day_of_year = f'{now.year:04d}-01-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_year}'")
    result = cursor.fetchone()
    if not result[0]:
        return "В этом году ещё нет расходов"
    all_today_expenses = result[0]
    result = _get_summary_amount_expenses(first_day_of_year, True)
    base_year_expenses = result[0] if result[0] else 0
    result = _get_summary_amount_expenses(first_day_of_year, False)
    minor_year_expenses = result[0] if result[0] else 0
    apartment_expenses = _get_apartment_expenses(first_day_of_year)
    return (f"Расходы в текущем году:\n"
            f"всего — {all_today_expenses} руб.\n"
            f"квартира — {apartment_expenses} руб. из {_get_apartment_limit() * now.month} руб.\n"
            f"второстепенные — {minor_year_expenses} руб. \n"
            f"базовые — {base_year_expenses} руб. из "
            f'''{(now.day * _get_budget_limit()) + ((now.month - 1) * 30 * _get_budget_limit())
                 + (_get_apartment_limit() * now.month)} руб.''')


def change_base(value: int):
    db.change_base_expense(value)
    cursor = db.get_cursor()
    cursor.execute("select daily_limit from budget where codename='base'")
    base = cursor.fetchone()
    return (f"Базовый расход изменен и составляет {base[0]} руб.")


def change_apartment_base(value: int):
    db.change_apartment_expense(value)
    cursor = db.get_cursor()
    cursor.execute("select daily_limit from budget where codename='apartment'")
    base = cursor.fetchone()
    return (f"Расход на квартиру изменен и составляет {base[0]} руб.")


def last_10() -> List[Expense]:
    """Возвращает последние несколько расходов"""
    cursor = db.get_cursor()
    cursor.execute(
        "select e.id, e.amount, c.name "
        "from expense e left join category c "
        "on c.codename=e.category_codename "
        "order by created desc limit 10")
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], amount=row[1], category_name=row[2]) for row in rows]
    return last_expenses


def last() -> List[Expense]:
    """Возвращает последние несколько расходов"""
    cursor = db.get_cursor()
    cursor.execute(
        "select e.id, e.amount, c.name "
        "from expense e left join category c "
        "on c.codename=e.category_codename "
        "order by created desc limit 1")
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], amount=row[1], category_name=row[2]) for row in rows]
    return last_expenses


def delete_expense(row_id: int) -> None:
    """Удаляет сообщение по его идентификатору"""
    db.delete("expense", row_id)


def _parse_message(raw_message: str) -> Message:
    """Парсит текст пришедшего сообщения о новом расходе."""
    regexp_result = re.match(r"([\d ]+) (.*)", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Не могу понять сообщение. Напишите сообщение в формате, "
            "например:\n1500 метро")

    amount = regexp_result.group(1).replace(" ", "")
    category_text = regexp_result.group(2).strip().lower()
    return Message(amount=int(amount), category_text=category_text)


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")


def _get_now_datetime() -> datetime.datetime:
    """Возвращает сегодняшний datetime с учётом времненной зоны Мск."""
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    return now


def _get_budget_limit() -> int:
    """Возвращает дневной лимит трат для основных базовых трат"""
    return db.fetchall("budget", ["daily_limit"])[0]["daily_limit"]


def _get_apartment_limit() -> int:
    """Возвращает лимит трат для трат на квартиру"""
    return db.fetchall("budget", ["daily_limit"])[1]["daily_limit"]


def _get_apartment_expenses(date: datetime) -> int:
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{date}' "
                   f"and category_codename = 'apartment'")
    apartment = cursor.fetchone()
    return apartment[0] if apartment[0] else 0


def _get_summary_amount_expenses(date: datetime, is_base: bool) -> tuple:
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{date}' "
                   f"and category_codename in (select codename "
                   f"from category where is_base_expense={is_base})")
    summary_amount = cursor.fetchone()
    return summary_amount


def _get_summary_amount_today_expenses(is_base: bool) -> tuple:
    cursor = db.get_cursor()
    cursor.execute("select sum(amount) "
                   "from expense where date(created)=date('now', 'localtime') "
                   "and category_codename in (select codename "
                   f"from category where is_base_expense={is_base})")
    summary_amount = cursor.fetchone()
    return summary_amount
