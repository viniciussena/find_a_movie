FROM apache/airflow:3.0.1

USER root

RUN apt-get update && apt-get install -y git

RUN mkdir -p /home/airflow/.ssh

COPY requirements.txt /requirements.txt

USER airflow

RUN pip install --no-cache-dir -r /requirements.txt