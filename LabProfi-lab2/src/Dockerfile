# Используем базовый образ Python 3.11
FROM python:3.11

RUN mkdir /backend_root
COPY ./ /backend_root
WORKDIR /backend_root

ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN apt-get update
RUN apt-get install -y librsvg2-bin
RUN apt-get install -y libxml2 libxml2-dev libxslt-dev libcairo2-dev pkg-config

# Устанавливаем poetry
RUN pip install poetry==1.4.2
RUN poetry config virtualenvs.create false 

# Устанавливаем зависимости
RUN poetry install --no-dev


RUN ./manage.py collectstatic --noinput
# Устанавливаем порт, который будет использоваться в контейнере
EXPOSE 8000