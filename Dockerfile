FROM python:3.10

WORKDIR /home

COPY . .

ENV TELEGRAM_API_TOKEN=""
ENV TELEGRAM_ACCESS_ID=""

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN pip install -U pip aiogram pytz python-dotenv && apt-get update && apt-get install sqlite3

VOLUME ["/home/db"]

ENTRYPOINT ["python", "server.py"]