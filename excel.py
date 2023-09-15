import pandas as pd
import datetime
import db
from typing import List, Tuple
from aiogram.types import FSInputFile


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


def _create_report() -> None:
    categories = db.get_all_categories()
    data = _get_report_data()
    months = [month[2] for month in data]
    months = list(dict.fromkeys(months))
    month_dict = {f'{month}': None for month in months}
    report_dict = {str(cat): {} for cat in categories}
    for cat in categories:
        report_dict[f'{cat}'].update(month_dict)
    for category in categories:
        for amount, cat, month in data:
            if not report_dict[f'{category}'][f'{month}']:
                report_dict[f'{category}'].update({f'{month}': int(amount) if category == cat else 0})
    df = pd.DataFrame.from_dict(report_dict, orient='index')
    with pd.ExcelWriter(r"report.xlsx", mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, sheet_name='расходы', startrow=0, startcol=0, index=True, header=True)


def get_report() -> FSInputFile:
    _create_report()
    return FSInputFile('report.xlsx', filename='отчет.xlsx')
