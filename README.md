Telegram бот для учёта личных расходов и ведения бюджета


В переменных окружения надо проставить API токен бота

`TELEGRAM_API_TOKEN` — API токен бота
`TELEGRAM_ACCESS_ID` — ID Telegram аккаунтов, от которого будут приниматься сообщения (сообщения от остальных аккаунтов игнорируются)
`PROXY_URL` — URL прокси сервера

Создание БД:
    sqlite3  finance.db < createdb.sql

