FROM python:3.12-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10

COPY requirements.txt /requirements.txt
COPY docker/requirements-streamlit.txt /docker/requirements-streamlit.txt
RUN pip install --no-cache-dir --timeout 100 --retries 10 -r /docker/requirements-streamlit.txt

COPY streamlit_app/ /app/
COPY src/ /app/src/

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]