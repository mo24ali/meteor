FROM apache/airflow:2.10.3

ARG AIRFLOW_UID=50000

USER root

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10

COPY requirements.txt /requirements.txt
RUN chmod a+r /requirements.txt

USER airflow

RUN pip install --no-cache-dir --timeout 100 --retries 10 -r /requirements.txt

RUN mkdir -p /opt/airflow/dags /opt/airflow/src /opt/airflow/data /opt/airflow/sql

ENV AIRFLOW_HOME=/opt/airflow