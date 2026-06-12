from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable # Airflow 변수 모듈 추가
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from google.cloud import bigquery
import os

# 1. GCP 인증 및 설정 (dags 폴더에 넣은 키 파일 경로)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/dags/bq_key.json"
GCP_PROJECT_ID = Variable.get("gcp_project_id") # Airflow Variable에서 프로젝트 ID 가져오기
BQ_DATASET_ID = Variable.get("bq_dataset_id") # Airflow Variable에서 데이터셋 ID 가져오기
BQ_TABLE_NAME = Variable.get("bq_table_name") # Airflow Variable에서 테이블 이름 가져오기

# 2. 실행할 파이프라인 함수
def run_stock_pipeline():
    target_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    client = bigquery.Client(project=GCP_PROJECT_ID)
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_NAME}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")

    for ticker_symbol in target_tickers:
        print(f"[{ticker_symbol}] 데이터 수집 시작...")
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="1d") # 매일 돌릴 거니까 오늘 하루치(1d)만!
        
        if df.empty:
            continue
            
        df.reset_index(inplace=True)
        df['Ticker'] = ticker_symbol
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df.columns = [c.lower() for c in df.columns]
        
        if 'dividends' in df.columns:
            df.drop(columns=['dividends', 'stock splits'], inplace=True, errors='ignore')

        # BigQuery 적재
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f" {ticker_symbol} 적재 완료!")

# 3. Airflow DAG 기본 설정
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5), # 실패 시 5분 뒤 재시도
}

# 4. DAG 정의 (매일 아침 9시(KST 기준 18시)에 실행)
with DAG(
    dag_id='us_stock_daily_pipeline',
    default_args=default_args,
    description='S&P 500 빅테크 5대장 주식 데이터 수집 및 BigQuery 적재',
    schedule_interval='0 9 * * *', 
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['stock', 'bigquery'],
) as dag:

    # 작업(Task) 선언
    extract_and_load_task = PythonOperator(
        task_id='extract_and_load_to_bq',
        python_callable=run_stock_pipeline,
    )