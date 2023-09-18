import os
import pandas as pd
import datetime
import db
from typing import List, Tuple
from aiogram.types import FSInputFile
import xlsxwriter
import matplotlib.pyplot as plt


def _get_report_data() -> List[Tuple]:
    now = datetime.datetime.now()
    first_day_of_year = f'{now.year:04d}-01-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount), name, "
                   f"case when strftime('%m', created) = '01' then 'Январь' "
                   f"when strftime('%m', created) = '02' then 'Февраль' "
                   f"when strftime('%m', created) = '03' then 'Март' "
                   f"when strftime('%m', created) = '04' then 'Апрель' "
                   f"when strftime('%m', created) = '05' then 'Май' "
                   f"when strftime('%m', created) = '06' then 'Июнь' "
                   f"when strftime('%m', created) = '07' then 'Июль' "
                   f"when strftime('%m', created) = '08' then 'Август' "
                   f"when strftime('%m', created) = '09' then 'Сентябрь' "
                   f"when strftime('%m', created) = '10' then 'Октябрь' "
                   f"when strftime('%m', created) = '11' then 'Ноябрь' "
                   f"else 'Декабрь' "
                   f"end as month "
                   f"from expense "
                   f"left join category on category_codename = codename "
                   f"where date(created) >= '{first_day_of_year}' "
                   f"group by month, name "
                   f"order by created asc")
    return cursor.fetchall()


def _get_stat(months: list, categories: list, data: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    month_stat = {f'{month}': [value[0] if month == value[2] else 0 for value in data] for month in months}
    for month in months:
        month_stat[f'{month}'] = (int(sum(month_stat[f'{month}'])))
    category_stat = {f'{cat}': [value[0] if cat == value[1] else 0 for value in data] for cat in categories}
    for cat in categories:
        category_stat[f'{cat}'] = (int(sum(category_stat[f'{cat}'])))
    category_stat = {k: v for k, v in category_stat.items() if v != 0}
    month_stat_df = pd.DataFrame.from_dict(month_stat, orient='index')
    category_stat_df = pd.DataFrame.from_dict(category_stat, orient='index')
    return month_stat_df, category_stat_df


def _create_excel_file() -> None:
    report = xlsxwriter.Workbook('report.xlsx')
    report.add_worksheet('расходы')
    report.close()


def _insert_stat_images(writer: pd.ExcelWriter) -> None:
    expenses = writer.sheets['расходы']
    expenses.insert_image('A22', 'months.png')
    expenses.insert_image('K22', 'categories.png')


def _create_stat_images(month_stat_df: pd.DataFrame, category_stat_df: pd.DataFrame) -> None:
    month_stat_df.plot(kind='bar', title='Ежемесячные траты', legend=False, color='g')
    plt.tight_layout()
    plt.savefig('months.png')
    category_stat_df.plot(kind='bar', title='Траты по категориям', legend=False, color='purple')
    plt.tight_layout()
    plt.savefig('categories.png')


def _delete_png_files():
    folder = os.listdir()
    for images in folder:
        if images.endswith(".png"):
            os.remove(images)


def _sort_data(categories: list, months: dict, data: list) -> dict:
    report_dict = {str(cat): {} for cat in categories}
    for cat in categories:
        report_dict[f'{cat}'].update(months)
    for category in categories:
        for amount, cat, month in data:
            if not report_dict[f'{category}'][f'{month}']:
                report_dict[f'{category}'].update({f'{month}': int(amount) if category == cat else 0})
    return report_dict


def _create_report() -> None:
    categories = db.get_all_categories()
    data = _get_report_data()
    months = [month[2] for month in data]
    months = list(dict.fromkeys(months))
    month_dict = {f'{month}': None for month in months}
    report_dict = _sort_data(categories, month_dict, data)
    month_stat_df, category_stat_df = _get_stat(months, categories, data)
    _create_excel_file()
    df = pd.DataFrame.from_dict(report_dict, orient='index')
    _create_stat_images(month_stat_df, category_stat_df)
    with pd.ExcelWriter(r"report.xlsx", mode='w', engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='расходы', startrow=0, startcol=0, index=True, header=True)
        _insert_stat_images(writer)
    _delete_png_files()


def get_report() -> FSInputFile:
    _create_report()
    return FSInputFile('report.xlsx', filename='отчет.xlsx')
