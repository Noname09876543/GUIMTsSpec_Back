FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN mkdir /backend_root
WORKDIR /backend_root
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
