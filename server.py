import asyncio
import logging
import sys
from os import getenv, remove
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
import exceptions
import expenses
from categories import Categories
from middlewares import AccessMiddleware
from aiogram.client.session.aiohttp import AiohttpSession
from excel import get_report

load_dotenv()

TOKEN = getenv("TELEGRAM_API_TOKEN")
ACCESS_ID = getenv("TELEGRAM_ACCESS_ID")
dp = Dispatcher()
dp.message.middleware.register(AccessMiddleware(ACCESS_ID.split(',')))
DEBUG = getenv("DEBUG")
if DEBUG == 'True':
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
else:
    session = AiohttpSession(proxy=getenv("PROXY_URL"))
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML, session=session)


@dp.message(Command('start', 'help', 'справка', 'помощь'))
async def send_welcome(message: types.Message):
    """Отправляет приветственное сообщение и помощь по боту"""
    await message.answer(
        "Бот для учёта финансов\n\n"
        "Добавить расход: добавить 250 такси\n"
        "Сегодняшняя статистика: /today\n"
        "За текущий месяц: /month\n"
        "За текущий год : /year\n"
        "Получить отчет в формате эксель: /report, /отчет\n"
        "Последние внесённые расходы: /expenses, /расходы\n"
        "Категории трат: /categories, /категории\n"
        "Изменить величину базового расхода: изменить базовый расход 2000")


@dp.message(lambda message: message.text.startswith('/del'))
async def del_expense(message: types.Message):
    """Удаляет одну запись о расходе по её идентификатору"""
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    answer_message = "Удалил"
    await message.answer(answer_message)


@dp.message(Command('categories', 'категории'))
async def categories_list(message: types.Message):
    """Отправляет список категорий расходов"""
    categories = Categories().get_all_categories()
    answer_message = "Категории трат:\n\n" + \
                     "Базовые расходы:\n*" + \
                     ("\n* ".join(
                         [c.name + ' (' + ", ".join(c.aliases) + ')' for c in categories if c.is_base_expense])) + \
                     "\n\nВторостепенные расходы:\n*" + \
                     ("\n* ".join(
                         [c.name + ' (' + ", ".join(c.aliases) + ')' for c in categories if not c.is_base_expense]))
    await message.answer(answer_message)


@dp.message(Command('today'))
async def today_statistics(message: types.Message):
    """Отправляет сегодняшнюю статистику трат"""
    answer_message = expenses.get_today_statistics()
    await message.answer(answer_message)


@dp.message(Command('month'))
async def month_statistics(message: types.Message):
    """Отправляет статистику трат текущего месяца"""
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


@dp.message(Command('year'))
async def year_statistics(message: types.Message):
    """Отправляет статистику трат текущего года"""
    answer_message = expenses.get_year_statistics()
    await message.answer(answer_message)


@dp.message(Command('report', 'отчет'))
async def send_report(message: types.Message):
    """Отправляет эксель файл"""
    report = get_report()
    await bot.send_document(chat_id=message.chat.id, document=report, caption='Отчет за прошедшие месяцы')
    remove('report.xlsx')


@dp.message(Command('expenses', 'расходы'))
async def list_expenses(message: types.Message):
    """Отправляет последние несколько записей о расходах"""
    last_expenses = expenses.last_10()
    if not last_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    last_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name} — нажми "
        f"/del{expense.id} для удаления"
        for expense in last_expenses]
    answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* " \
        .join(last_expenses_rows)
    await message.answer(answer_message)


@dp.message(lambda message: message.text.startswith(('добавить', 'Добавить')))
async def add_expense(message: types.Message):
    """Добавляет новый расход"""
    try:
        expense = expenses.add_expense(message.text[8:])
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
        f"Удалить последнюю трату {expenses.last()[0].amount} руб на {expenses.last()[0].category_name}: "
        f"/del{expenses.last()[0].id}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.answer(answer_message)


@dp.message(lambda message: message.text.startswith(('изменить базовый расход')))
async def change_base(message: types.Message):
    """Изменяет базовый расход"""
    try:
        answer_message = expenses.change_base(int(message.text[23:]))
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    await message.answer(answer_message)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
