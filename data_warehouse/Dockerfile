FROM apache/superset:latest

USER root

# venv에 pip 설치 후 venv 안에 직접 패키지 설치
RUN /app/.venv/bin/python -m ensurepip && \
    /app/.venv/bin/python -m pip install --no-cache-dir \
    sqlalchemy-bigquery \
    google-cloud-bigquery \
    google-cloud-bigquery-storage \
    db-dtypes \
    pyarrow

USER superset